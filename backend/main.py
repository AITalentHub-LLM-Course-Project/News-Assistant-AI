from fastapi import FastAPI
from pydantic import BaseModel
from backend.llm_inference import generate_response

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(query: Query):
    response = generate_response(query.question)
    return {"answer": response}