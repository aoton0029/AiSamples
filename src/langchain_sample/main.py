import torch
from transformers import AutoTokenizer, AutoModel
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
from langchain.document_loaders import TextLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import os

class RAGSystem:
    def __init__(self, model_name="microsoft/DialoGPT-medium"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # 埋め込みモデルの初期化
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # 生成モデルの初期化
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # パイプラインの作成
        self.text_generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=512,
            temperature=0.7,
            do_sample=True,
            device=0 if torch.cuda.is_available() else -1
        )
        
        self.llm = HuggingFacePipeline(pipeline=self.text_generator)
        self.vectorstore = None
        self.qa_chain = None
    
    def load_documents(self, file_path):
        """ドキュメントを読み込んでベクトル化"""
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        
        # テキストを分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        texts = text_splitter.split_documents(documents)
        
        # ベクトルストアの作成
        self.vectorstore = FAISS.from_documents(texts, self.embeddings)
        
        # QAチェーンの作成
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        
        print(f"Loaded {len(texts)} text chunks")
    
    def query(self, question):
        """質問に対して回答を生成"""
        if self.qa_chain is None:
            return "ドキュメントが読み込まれていません。"
        
        result = self.qa_chain({"query": question})
        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }
    
    def save_vectorstore(self, path):
        """ベクトルストアを保存"""
        if self.vectorstore:
            self.vectorstore.save_local(path)
    
    def load_vectorstore(self, path):
        """ベクトルストアを読み込み"""
        self.vectorstore = FAISS.load_local(path, self.embeddings)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )

# 使用例
def main():
    # RAGシステムの初期化
    rag = RAGSystem()
    
    # サンプルテキストファイルの作成
    sample_text = """
    機械学習は人工知能の一分野です。
    機械学習では、データからパターンを学習してタスクを実行します。
    深層学習は機械学習の手法の一つで、ニューラルネットワークを使用します。
    PyTorchは深層学習フレームワークの一つです。
    """
    
    with open("sample_data.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)
    
    # ドキュメントの読み込み
    rag.load_documents("sample_data.txt")
    
    # 質問応答のテスト
    questions = [
        "機械学習とは何ですか？",
        "PyTorchについて教えてください",
        "深層学習の特徴は？"
    ]
    
    for question in questions:
        print(f"\n質問: {question}")
        result = rag.query(question)
        print(f"回答: {result['answer']}")
        print("参照元:", [doc.page_content[:100] for doc in result['source_documents']])

if __name__ == "__main__":
    main()