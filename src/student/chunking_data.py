
from student.classes_types import Chunk
from typing import List
import re
import ast
import os
from tqdm import tqdm



PYTHON_EXTENSIONS = {".py"}
TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".toml"}
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".o", ".a", ".lib", ".dll", ".exe",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".zip", ".tar", ".gz", ".bz2", ".whl",
    ".bin", ".pt", ".pth", ".onnx", ".pb",
    ".lock"
}


def offset_lines_func(lines: List[str]) -> List[int]:
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line) + 1)
    return offsets


def split_large_chunk(
    file_path: str, content: str, start_offset: int,
    max_chunk_size: int, chunk_type: str) -> List[Chunk]:

    lines = content.split("\n")
    chunk = ""
    offset = start_offset
    result = []

    for ln in lines:

        ln_with_newline = ln + "\n"
        if len(chunk) + len(ln_with_newline) <= max_chunk_size:
            chunk += ln_with_newline
        
        else:
            if chunk.strip():
                obj = Chunk(file_path=file_path,
                            content=chunk,
                            first_character_index=offset,
                            last_character_index=len(chunk) + offset,
                            chunk_type=chunk_type
                        )
                result.append(obj)

            offset += len(chunk)
            chunk = ln_with_newline

    if chunk.strip():
        obj = Chunk(file_path=file_path,
                    content=chunk,
                    first_character_index=offset,
                    last_character_index=len(chunk) + offset,
                    chunk_type=chunk_type
                )
        result.append(obj)
    return result




def chunking_text_string_file(file_path: str, content: str, max_chunk_size: int = 2000) -> List[Chunk]:
    result: List[Chunk] = []

    if len(content) <= max_chunk_size:
        if content.strip():
            obj = Chunk(
                file_path=file_path,
                content=content,
                first_character_index=0,
                last_character_index=len(content),
                chunk_type="text"
            )
            result.append(obj)
        return result

    pattern_of_split = r"(?=^#{1,3} |\n\n)"
    lst = re.split(pattern_of_split, content, flags=re.MULTILINE)
    chunk = ""
    start = 0

    for element in lst:
        if element == "":
            continue

        if len(chunk) + len(element) <= max_chunk_size:
            chunk += element

        else:
            if chunk.strip():
                obj = Chunk(
                    file_path=file_path,
                    content=chunk,
                    first_character_index=start,
                    last_character_index=start + len(chunk),
                    chunk_type="text"
                )
                result.append(obj)

            if len(element) > max_chunk_size:
                inner_chunks = split_large_chunk(file_path, element, start + len(chunk), max_chunk_size, "text")
                result.extend(inner_chunks)
                start = start + len(chunk) + len(element)
                chunk = ""

            else:
                start = start + len(chunk)
                chunk = element

    if chunk.strip():
        obj = Chunk(
            file_path=file_path,
            content=chunk,
            first_character_index=start,
            last_character_index=start + len(chunk),
            chunk_type="text"
        )
        result.append(obj)
    return result






def chunk_code_string_file(file_path: str, content: str, max_chunk_size: int = 2000) -> List[Chunk]:
    result: List[Chunk] = []
    
    try:

        tree = ast.parse(content)
        
        top_level = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                top_level.append(node)
        
        if not top_level:
            return chunking_text_string_file(file_path, content, max_chunk_size)
        
        lines = content.split("\n")
        offsets = offset_lines_func(lines)

        for node in top_level:
            start_line = node.lineno - 1
            end_line = node.end_lineno

            start_char = offsets[start_line]
            if end_line < len(offsets):
                end_char = offsets[end_line]
            else:
                end_char = len(content)
            
            node_content = (content[start_char:end_char])
            
            if len(node_content) > max_chunk_size:
                inner_chunks = split_large_chunk(file_path, node_content, start_char, max_chunk_size, "python")
                if len(inner_chunks) > 0:
                    result.extend(inner_chunks)
            else:
                obj = Chunk(
                file_path=file_path,
                content=node_content,
                first_character_index=start_char,
                last_character_index=end_char,
                chunk_type="python"
            )
                result.append(obj)

        if top_level:
            first_node_start_index = offsets[top_level[0].lineno - 1]
            if first_node_start_index > 0:
                above_data = content[:first_node_start_index].strip()
                if above_data:
                    above_chunks = split_large_chunk(file_path, above_data, 0, max_chunk_size, "python")
                    result = above_chunks + result

    except SyntaxError:
        return chunking_text_string_file(file_path, content, max_chunk_size)
    
    if not result:
        return chunking_text_string_file(file_path, content, max_chunk_size)
    
    return result



# node_modules/build/dist
def chunk_repository(repo_path: str, max_chunk_size: int = 2000) -> List[Chunk]:

    res_output: List[Chunk] = []
    all_files_path: List[str] = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__", ".git"}]
        
        for file in files:
            extention = os.path.splitext(file)[1].lower()
            #skip
            if extention in SKIP_EXTENSIONS:
                continue
            if extention not in PYTHON_EXTENSIONS and extention not in TEXT_EXTENSIONS:
                continue

            full_path_from_data_root = os.path.join(root, file)
            all_files_path.append(full_path_from_data_root)

    for the_path in tqdm(all_files_path, desc="Currently Chunking Progress"):
        try:
            with open(the_path, "r", encoding="utf-8", errors="ignore") as f:
                content_file_data = f.read()

            if not content_file_data.strip():
                continue
            
            extention = os.path.splitext(the_path)[1].lower()
            
            if extention in PYTHON_EXTENSIONS:
                res_chunks = chunk_code_string_file(the_path, content_file_data, max_chunk_size)
                
            elif extention in TEXT_EXTENSIONS:
                res_chunks = chunking_text_string_file(the_path, content_file_data, max_chunk_size)

            #imposible exec
            else:
                continue

            res_output.extend(res_chunks)
            
        except Exception as err:
            print(f"Error: While Process in Chunking Stage, Reason {err}")
        
    return res_output
