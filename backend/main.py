from fastapi import FastAPI
from pydantic import BaseModel
from backend.llm_inference import LLMInference

app = FastAPI()

class Query(BaseModel):
    question: str

llm_inference = LLMInference()

@app.post("/ask")
async def ask_question(query: Query):
    response = llm_inference.generate_response(query.question)
    return {"answer": response}