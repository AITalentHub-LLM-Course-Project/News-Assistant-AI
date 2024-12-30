#!/bin/bash

rm -f news.db

python -m backend.launcher &

sleep 15
# run FastAPI backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# run frontend
streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0