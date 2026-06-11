import re
from typing import List
import os
from student.chunking_data import chunk_repository
import json
from tqdm import tqdm
from rank_bm25 import BM25Okapi


CHUNKS_PATH = "data/processed/chunks/chunks.json"
BM25_INDEX_PATH = "data/processed/bm25_index/bm25.pkl"
CORPUS_PATH = "data/processed/bm25_index/corpus.pkl"



# this function is fully modyfieded
def my_tokenizer(text: str) -> List[str]:
    
    text = text.replace("_", " ")
    
    #this pattern like for classes names: "GPUWorker, LLMEngine SQLDatabase"
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)

    # for the search meaning
    text = text.lower()
    
    # for remove any this is not a alpha or digit or newline, space, tab:
    text = re.sub(r"[^\w\s]", " ", text)
    
    #split() splits on spaces tabs newlines with get a strip
    tokens_list = [elem for elem in text.split() if len(elem) > 1]
    
    return tokens_list

    
def build_the_indexed_stock(repo_path: str = "data/raw/vllm-0.10.1", max_chunk_size: int = 2000) -> None:
    
    print(f"\nStart Indexing The Repo: {repo_path}\n")

    os.makedirs("data/processed/chunks", exist_ok=True)
    os.makedirs("data/processed/bm25_index", exist_ok=True)
    
    all_chunks_result = chunk_repository(repo_path, max_chunk_size)
    print(f"THERE ARE {len(all_chunks_result)} chunks THAT CREATED NOW.\n")
    
    print(f"\nStart Saving Them(chunks) To The File Path -> {CHUNKS_PATH}")
    list_of_chunks_dictionries = []
    for chunk_obj in all_chunks_result:
        list_of_chunks_dictionries.append(chunk_obj.model_dump())
    
    
    with open(CHUNKS_PATH, "w", encoding="utf-8") as file:
        as_string = json.dumps(list_of_chunks_dictionries, indent=2, ensure_ascii=False)
        file.write(as_string)
        print("AER SAVED.\n")


    print("START BUILDING BM25 index...")
    tokens_list_result = []
    for chunk_obj in tqdm(all_chunks_result, desc="THE TOKENIZER progress bar"):
        lst = my_tokenizer(chunk_obj.content)
        tokens_list_result.append(lst)

    bm25_result = BM25Okapi(tokens_list_result)
    
    print(type(bm25_result))
    
    
    
    
    
build_the_indexed_stock()
