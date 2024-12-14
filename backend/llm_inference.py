from langchain.chains import LLMChain
from transformers import pipeline

generator = pipeline('text-generation', model='distilgpt2')

def generate_response(prompt: str) -> str:
    # response = generator(prompt, max_length=50, num_return_sequences=1)
    # return response[0]['generated_text']
    return "Test Answer"

if __name__ == "__main__":
    prompt = "What is the latest news in trading?"
    response = generate_response(prompt)
    print(response)