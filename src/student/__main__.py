from student.classes_types import AnsweredQuestion, MinimalSource
import uuid


lst = [
    MinimalSource(file_path="/lp/vc", first_character_index=2, last_character_index=25),
    MinimalSource(file_path="/lp/vsw.py", first_character_index=0, last_character_index=100),
]


try:
    obj = AnsweredQuestion(question="koko cv?", sources=lst, answer="hmdlh")
except Exception as e:
    print(e)


