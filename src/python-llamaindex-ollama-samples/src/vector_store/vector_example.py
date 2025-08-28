class VectorStoreExample:
    def __init__(self):
        self.vector_store = {}

    def add_vector(self, key, vector):
        self.vector_store[key] = vector

    def retrieve_vector(self, key):
        return self.vector_store.get(key, None)