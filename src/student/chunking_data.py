
from student.classes_types import Chunk
from typing import List
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


def split_large_chunk(file_path: str, content: str, start_offset: int, max_chunk_size: int, chunk_type: str) -> List[Chunk]:
    chunks = []
    lines = content.split("\n")
    current_chunk = ""
    current_start = start_offset

    for line in lines:
        line_with_newline = line + "\n"
        if len(current_chunk) + len(line_with_newline) <= max_chunk_size:
            current_chunk += line_with_newline
        else:
            if current_chunk.strip():
                chunks.append(Chunk(
                    file_path=file_path,
                    content=current_chunk,
                    first_character_index=current_start,
                    last_character_index=current_start + len(current_chunk),
                    chunk_type=chunk_type,
                ))
            current_start += len(current_chunk)
            current_chunk = line_with_newline

    if current_chunk.strip():
        chunks.append(Chunk(
            file_path=file_path,
            content=current_chunk,
            first_character_index=current_start,
            last_character_index=current_start + len(current_chunk),
            chunk_type=chunk_type,
        ))

    return chunks





c = "li1\nmff\nrp"

res = split_large_chunk("y", c, 0, 10, "")

for o in res:
    print("\ntypee: %s" % o.chunk_type)
    print("content: %s" % o.content)
    print("path: %s" % o.file_path)
    print("start: %d" % o.first_character_index)
    print("end: %d" % o.last_character_index)
    print("*" * 20)


