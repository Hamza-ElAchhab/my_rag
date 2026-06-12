from transformers import AutoModelForCausalLM, AutoTokenizer
from student.classes_types import MinimalSource
import torch


# prompt = f"""
# You are a code assistant specialized in understanding software repositories.

# Answer the question using ONLY the provided context.

# Rules:
# - Do not use external knowledge.
# - If the answer is not in the context, say "I don't know based on the provided context".
# - Keep the answer concise and technical.
# - Mention relevant source file paths when possible.

# Context:
# {context}

# Question:
# {question}

# Answer:
# """


model = None
tokenizer = None
MODEL_NAME = "Qwen/Qwen3-0.6B"


def loading_the_model() -> None:
    
    global model, tokenizer
    
    if model is not None:
        return
    
    print(f"\nSTART LOADING THE MODEL {MODEL_NAME}\n")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float32, device_map="auto", trust_remote_code=True
    )
    
    model.eval()
    print("Model loaded successfully.")


loading_the_model()
