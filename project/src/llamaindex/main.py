from fastapi import FastAPI
from llama_index import GPTSimpleVectorIndex

app = FastAPI()

# Initialize the LlamaIndex
index = GPTSimpleVectorIndex()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "description": "This is an item."}

@app.post("/items/")
def create_item(item: dict):
    # Logic to create an item
    return {"message": "Item created", "item": item}