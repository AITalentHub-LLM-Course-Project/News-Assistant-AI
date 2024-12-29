import streamlit as st
import requests
from datetime import datetime

st.title("Trading News Chatbot")

question = st.text_input("Ask a question about trading news:")

# Add date input widgets
start_date = st.date_input("Start Date", value=datetime.now().date())
end_date = st.date_input("End Date", value=datetime.now().date())

if st.button("Submit"):
    if question:
        # Convert dates to string format
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Include dates in the request
        response = requests.post("http://localhost:8000/ask", json={
            "question": question,
            "start_date": start_date_str,
            "end_date": end_date_str
        })
        
        if response.status_code == 200:
            answer = response.json().get("answer")
            st.write(f"Answer: {answer}")
        else:
            st.write("Error: Could not get a response from the server.")
    else:
        st.write("Please enter a question.")
