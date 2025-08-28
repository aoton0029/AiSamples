# python-llamaindex-ollama-samples

This project demonstrates the integration of LlamaIndex and Ollama for various applications, including basic chat functionality, document question answering, and vector storage and retrieval.

## Project Structure

```
python-llamaindex-ollama-samples
├── src
│   ├── __init__.py
│   ├── basic_chat
│   │   └── chat_example.py
│   ├── document_qa
│   │   └── qa_example.py
│   ├── vector_store
│   │   └── vector_example.py
│   └── utils
│       └── helpers.py
├── data
│   └── sample_documents.txt
├── requirements.txt
├── config.py
└── README.md
```

## Installation

To get started, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/python-llamaindex-ollama-samples.git
cd python-llamaindex-ollama-samples
pip install -r requirements.txt
```

## Usage

### Basic Chat

To use the basic chat functionality, navigate to the `src/basic_chat` directory and run the `chat_example.py` script. This will start a chat session where you can send messages and receive responses.

### Document Question Answering

For document question answering, you can utilize the `qa_example.py` script located in the `src/document_qa` directory. This script allows you to load documents and ask questions based on their content.

### Vector Storage and Retrieval

The `vector_example.py` script in the `src/vector_store` directory demonstrates how to add and retrieve vectors using LlamaIndex and Ollama. This is useful for applications that require vector-based data storage and retrieval.

## Sample Documents

Sample documents for testing are provided in the `data/sample_documents.txt` file. You can modify this file to include your own documents for testing purposes.

## Configuration

Configuration settings, such as API keys and other constants, can be found in the `config.py` file. Make sure to update this file with your specific settings before running the examples.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.