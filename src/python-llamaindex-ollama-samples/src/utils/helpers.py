def load_sample_documents(file_path):
    with open(file_path, 'r') as file:
        documents = file.readlines()
    return [doc.strip() for doc in documents]

def format_output(response):
    return f"Response: {response}"