import os
from langchain.chat_models.gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage


class LLMInference:
    def __init__(self):
        self.api_key = os.getenv('GIGACHAT_API_KEY')
        self.model_name = os.getenv('GIGACHAT_MODEL_NAME')
        
        if not self.api_key or not self.model_name:
            raise ValueError("API key and model name must be set in environment variables.")
        
        self.model = GigaChat(
            api_key=self.api_key,
            model_name=self.model_name,
            timeout=30,
            verify_ssl_certs=False
        )

    def generate_response(self, prompt: str) -> str:
        try:
            response = self.model.invoke(prompt)
            return response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "An error occurred while generating the response."

if __name__ == "__main__": # for testing
    messages = [
        SystemMessage(content="You are a helpful assistant."), # TODO: add good system prompt
    ]
    llm_inference = LLMInference()

    while True:
        user_message = input("User: ")
        if user_message.lower() in ['exit', 'quit']:
            break
        messages.append(HumanMessage(content=user_message))

        response = llm_inference.generate_response(messages)
        messages.append(response)
        print("Assistant: ", response)