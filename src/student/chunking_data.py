
from student.classes_types import Chunk
from typing import List
import re
import ast
import os
from tqdm import tqdm


PYTHON_EXTENSIONS = {".py"}
TEXT_EXTENSIONS = {".md", ".rst", ".txt", ".yaml", ".yml", ".toml", ".cfg", ".ini"}
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".o", ".a", ".lib", ".dll", ".exe",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".zip", ".tar", ".gz", ".bz2", ".whl",
    ".bin", ".pt", ".pth", ".onnx", ".pb",
    ".lock"
}


def lines_offsets(lines: List[str]) -> List[int]:
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
    res = []

    for ln in lines:

        ln_with_newline = ln + "\n"
        if len(chunk) + len(ln_with_newline) <= max_chunk_size:
            chunk += ln_with_newline
        
        else:
            if chunk.strip():
                obj = Chunk(file_path=file_path, content=chunk,first_character_index=offset,
                            last_character_index=len(chunk) + offset, chunk_type=chunk_type)
                res.append(obj)
            
            offset += len(chunk)
            chunk = ln_with_newline

    if chunk.strip():
        obj = Chunk(file_path=file_path, content=chunk,first_character_index=offset,
                    last_character_index=len(chunk) + offset, chunk_type=chunk_type)
        res.append(obj)
    return res




def chunk_text_file(file_path: str, content: str, max_chunk_size: int = 2000) -> List[Chunk]:
    res: List[Chunk] = []

    # Small file: return a single chunk
    if len(content) <= max_chunk_size:
        if content.strip():
            obj = Chunk(
                file_path=file_path,
                content=content,
                first_character_index=0,
                last_character_index=len(content),
                chunk_type="text"
            )
            res.append(obj)
        return res

    pattern_of_split = r'(?=^#{1,3} |\n\n)'
    lst = re.split(pattern_of_split, content, flags=re.MULTILINE)
    chunk = ""
    start = 0

    for ele in lst:
        if ele == "":
            continue

        if len(chunk) + len(ele) <= max_chunk_size:
            chunk += ele

        else:
            if chunk.strip():
                obj = Chunk(
                    file_path=file_path,
                    content=chunk,
                    first_character_index=start,
                    last_character_index=start + len(chunk),
                    chunk_type="text"
                )
                res.append(obj)

            if len(ele) > max_chunk_size:
                inner_chunks = split_large_chunk(
                    file_path=file_path,
                    content=ele,
                    start_offset=start + len(chunk),
                    max_chunk_size=max_chunk_size,
                    chunk_type="text"
                )

                res.extend(inner_chunks)
                start = start + len(chunk) + len(ele)
                chunk = ""

            else:
                start = start + len(chunk)
                chunk = ele

    if chunk.strip():
        obj = Chunk(
            file_path=file_path,
            content=chunk,
            first_character_index=start,
            last_character_index=start + len(chunk),
            chunk_type="text"
        )
        res.append(obj)
    return res






def chunk_python_file(file_path: str, content: str, max_chunk_size: int = 2000) -> List[Chunk]:
    res: List[Chunk] = []
    
    try:

        tree = ast.parse(content)
        
        top_level = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                top_level.append(node)
        
        if not top_level:
            return chunk_text_file(file_path, content, max_chunk_size)
        
        lines = content.split("\n")
        offsets = lines_offsets(lines)

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
                    res.extend(inner_chunks)
            
            else:
                obj = obj = Chunk(
                file_path=file_path,
                content=node_content,
                first_character_index=start_char,
                last_character_index=end_char,
                chunk_type="python"
            )
                res.append(obj)

        if top_level:
            first_node_start_index = offsets[top_level[0].lineno - 1]
            if first_node_start_index > 0:
                above_data = content[:first_node_start_index].strip()
                if above_data:
                    above_chunks = split_large_chunk(file_path, above_data, 0, max_chunk_size, "python")
                    res = above_chunks + res

    except SyntaxError:
        return chunk_text_file(file_path, content, max_chunk_size)
    
    if not res:
        return chunk_text_file(file_path, content, max_chunk_size)
    
    return res




def chunk_repository(repo_path: str, max_chunk_size: int = 2000) -> List[Chunk]:

    res_output: List[Chunk] = []
    all_files = []

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
            all_files.append(full_path_from_data_root)

    for the_path in tqdm(all_files, desc="Currently Chunking Progress"):
        try:
            with open(the_path, "r") as f:
                content_data = f.read()
                
            if not content_data.strip():
                continue
            
            extention = os.path.splitext(the_path)[1].lower()
            
            if extention in PYTHON_EXTENSIONS:
                res_chunks = chunk_python_file(the_path, content_data, max_chunk_size)
                
            if extention in TEXT_EXTENSIONS:
                res_chunks = chunk_text_file(the_path, content_data, max_chunk_size)
            
            res_output.extend(res_chunks)
            
        except Exception as err:
            print(f"Error: While Process in Chunking Stage, Reason {err}")
        
    return res_output

            
            
                
                
        



print(len(chunk_repository("data/raw/vllm-0.10.1")))


#             ext = os.path.splitext(fpath)[1].lower()
#             if ext in PYTHON_EXTENSIONS:
#                 chunks = chunk_python_file(fpath, content, max_chunk_size)
#             else:
#                 chunks = chunk_text_file(fpath, content, max_chunk_size)

#             all_chunks.extend(chunks)

#         except Exception as e:
#             print(f"Warning: could not process {fpath}: {e}")

#     return all_chunks


