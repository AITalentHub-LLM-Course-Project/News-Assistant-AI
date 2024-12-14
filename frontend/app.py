import streamlit as st
import requests

st.title("Trading News Chatbot")

question = st.text_input("Ask a question about trading news:")

if st.button("Submit"):
    if question:
        response = requests.post("http://localhost:8000/ask", json={"question": question})
        if response.status_code == 200:
            answer = response.json().get("answer")
            st.write(f"Answer: {answer}")
        else:
            st.write("Error: Could not get a response from the server.")
    else:
        st.write("Please enter a question.")