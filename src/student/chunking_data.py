
from student.classes_types import Chunk
from typing import List
import re
import ast


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
                obj = Chunk(file_path, node_content, start_char, end_char, "python")
                res.append(obj)

        if top_level:
            first_node_start_index = offsets[top_level[0].lineno - 1]
            if first_node_start_index > 0:
                above_data = content[:first_node_start_index].strip()
                if above_data:
                    above_chunks = split_large_chunk(file_path, above_data, 0, max_chunk_size, "python")
                    res = res + above_chunks

    except SyntaxError:
        return chunk_text_file(file_path, content, max_chunk_size)
    
    if not res:
        return chunk_text_file(file_path, content, max_chunk_size)
    
    return res



content = """import sys

class koko:
    def get():
        return 2

def greet(name):
    print("Hello %s" % name)"""




# res = chunk_python_file("file", content, max_chunk_size=10)


# for o in res:
#     print(o.chunk_type)
#     print(o.first_character_index)
#     print(o.last_character_index)
#     print(o.content)
#     print(o.file_path)
#     print("=" * 40)

s = """my name


is hamza"""

print(s.split("\n"))