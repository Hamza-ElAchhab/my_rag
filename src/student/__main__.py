from student.indexing_stage import load_indexed_data_from_disk, retrieve
from student.the_generation import generate_the_answer



bm, ch = load_indexed_data_from_disk()

query = "what is paged attention"

res = retrieve(query, bm, ch)


for o in res:
    print(o.file_path)
    print(o.first_character_index)
    print(o.last_character_index)
    print("="*50)


sttr = generate_the_answer(query, res, max_new_tokens=100)

print(sttr)
