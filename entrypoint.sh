#!/bin/bash

if [ "$1" = 'llm_api' ]; then

    python3 backend/news_fetcher.py

    # run FastAPI backend
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

    # run frontend
    streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0

else

    exec "$@"

fi
