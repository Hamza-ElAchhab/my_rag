import re
from typing import List
import os
from student.chunking_data import chunk_repository
import json
from tqdm import tqdm
from rank_bm25 import BM25Okapi
import pickle
from typing import Tuple
from student.classes_types import Chunk, MinimalSource
import numpy


CHUNKS_PATH = "data/processed/chunks/chunks.json"
BM25_INDEX_PATH = "data/processed/bm25_index/bm25.pkl"
TOKENS_LISTS = "data/processed/bm25_index/tokenslists.pkl"



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
    
    with open(BM25_INDEX_PATH, "wb") as file:
        binarries_bytes = pickle.dumps(bm25_result)
        file.write(binarries_bytes)
        print(f"\n\nCREATED BM25 FILE DATABASE. path {BM25_INDEX_PATH}\n")

    # cache memory if data lose, and for not create tokens again
    with open(TOKENS_LISTS, "wb") as file:
        binarries_bytes = pickle.dumps(tokens_list_result)
        file.write(binarries_bytes)
        print(f"CREATED CACHE MEMORY FILE FOR TOKENS. path {TOKENS_LISTS}\n")
    print()
    print("="*62)
    print("Ingestion complete! data saved under root: data/processed/...")
    print("="*62)
    print()





#prepare for retrival
#and retrival
#i think these should put them in a single file

def load_indexed_data_from_disk() -> Tuple[BM25Okapi, List[Chunk]]:
    if not os.path.exists(BM25_INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError("Error, Program Still Does not Have any indexed data")
    
    with open(BM25_INDEX_PATH, "rb") as file:
        bm25 = pickle.loads(file.read())

    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        chunks_as_string = file.read()
        list_of_chunks = json.loads(chunks_as_string)
    
    list_of_chunks_obj = []
    for ch_dict in list_of_chunks:
        list_of_chunks_obj.append(Chunk(**ch_dict))
    
    return bm25, list_of_chunks_obj



def retrieve(query: str, bm25: BM25Okapi, chunks: List[Chunk], k: int = 10) -> List[MinimalSource]:

    tokenize_query = my_tokenizer(query)
    scores = bm25.get_scores(tokenize_query)
    
    best_k_indexes = numpy.argsort(scores)[::-1][:k]
    
    result = []
    scores_cache: set = set()
    
    for idx in best_k_indexes:
        chunk_obj = chunks[idx]

        build_key = (chunk_obj.file_path, chunk_obj.first_character_index, chunk_obj.last_character_index)
        if build_key in scores_cache:
            continue
        scores_cache.add(build_key)
        
        obj = MinimalSource(file_path=chunk_obj.file_path,
                            first_character_index=chunk_obj.first_character_index,
                            last_character_index=chunk_obj.last_character_index
                        )
        result.append(obj)

    return result[:k]









res = retrieve("paged attention implementation", load_indexed_data_from_disk()[0], load_indexed_data_from_disk()[1])

print("length : %d\n\n" % len(res))

for o in res:
    print("start: %d" % o.first_character_index)
    print("end: %d" % o.last_character_index)
    print("file: %s" % o.file_path)
    print("="*50)
