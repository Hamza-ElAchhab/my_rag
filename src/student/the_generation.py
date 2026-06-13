from transformers import AutoModelForCausalLM, AutoTokenizer
from student.classes_types import MinimalSource
import torch
from typing import List







#load model, tokenizer objs
model = None
tokenizer = None
MODEL_NAME = "Qwen/Qwen3-0.6B"


def loading_the_model() -> None:
    
    global model, tokenizer
    
    # if already exists
    if model is not None:
        return
    
    print(f"\nSTART LOADING THE MODEL {MODEL_NAME}\n")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float32, device_map="auto", trust_remote_code=True)
    
    #force to remove training mode
    model.eval()
    print("Model loaded successfully.")




def get_content_from_source_obj(source_obj: MinimalSource, max_context_length: int = 2000) -> str:
    try:
        with open(source_obj.file_path, "r", encoding="utf-8", errors="ignore") as file:
            file.seek(source_obj.first_character_index)
            length = source_obj.last_character_index - source_obj.first_character_index

            if length >= max_context_length:
                length = max_context_length
            
            string_text_content = file.read(length)
        
        return string_text_content
    except Exception:
        return ""




def generate_the_answer(user_question: str, sources: List[MinimalSource],
                        max_context_length: int = 2000, max_new_tokens: int = 256
    ) -> None:
    
    loading_the_model()
    
    list_of_readed_contents = []
    
    i = 1
    for source_obj in sources[:5]:
        the_content = get_content_from_source_obj(source_obj, max_context_length)
        if the_content:
            list_of_readed_contents.append(f"[Source {i+1}: {source_obj.file_path}]\n{the_content}")
    
    big_marge_context = "\n\n".join(list_of_readed_contents)

    the_prompt = f"""
    You are a code assistant specialized in understanding software repositories.

    Answer the question using ONLY the provided context.

    Rules:
    - Do not use external knowledge.
    - If the answer is not in the context, say "I don't know based on the provided context".
    - Keep the answer concise and technical.
    - Mention relevant source file paths when possible.

    Context:
    {big_marge_context}

    Question:
    {user_question}

    Answer:
    """
    
    try:
        inputs = tokenizer(the_prompt, return_tensors="pt", truncation=True, max_length=2048)
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(  # type: ignore
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=tokenizer.eos_token_id,  # type: ignore
            )
        
        input_len = inputs["input_ids"].shape[1]
        new_tokens = outputs[0][input_len:]
        answer = tokenizer.decode(new_tokens, skip_special_tokens=True)  # type: ignore
        return answer.strip()

    except Exception as e:
        return f"Error generating answer: {e}"


