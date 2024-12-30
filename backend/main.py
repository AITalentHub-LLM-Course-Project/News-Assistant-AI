from fastapi import FastAPI
from pydantic import BaseModel
from backend.llm_inference import LLMInference
from datetime import datetime

app = FastAPI()

class Query(BaseModel):
    question: str
    start_date: str
    end_date: str

llm_inference = LLMInference()

@app.post("/ask")
async def ask_question(query: Query):
    # Convert string dates to datetime objects
    start_date = datetime.strptime(query.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(query.end_date, "%Y-%m-%d")
    
    # Pass the dates to the generate_response method
    response = llm_inference.generate_response(query.question, start_date, end_date)
    return {"answer": response}