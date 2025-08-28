class ChatExample:
    def __init__(self):
        self.history = []

    def start_chat(self):
        print("Chat started. Type 'exit' to end the chat.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Chat ended.")
                break
            response = self.send_message(user_input)
            print(f"Bot: {response}")

    def send_message(self, message):
        # Here you would integrate with LlamaIndex and Ollama to get a response
        # For demonstration, we'll just echo the message back
        self.history.append(message)
        return f"You said: {message}"