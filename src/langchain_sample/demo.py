import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
import numpy as np
from typing import List
import json

class CustomEmbeddings(Embeddings):
    """カスタム埋め込みクラス（PyTorchモデル使用）"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """複数のドキュメントを埋め込み"""
        embeddings = []
        for text in texts:
            embedding = self._embed_single(text)
            embeddings.append(embedding.tolist())
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """単一のクエリを埋め込み"""
        embedding = self._embed_single(text)
        return embedding.tolist()
    
    def _embed_single(self, text: str) -> torch.Tensor:
        """単一テキストの埋め込み処理"""
        with torch.no_grad():
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True, 
                padding=True
            ).to(self.device)
            
            outputs = self.model(**inputs)
            # 平均プーリング
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            
            # 正規化
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            return embeddings.squeeze()

class AdvancedRAGSystem:
    """高度なRAGシステム"""
    
    def __init__(self, embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        self.embeddings = CustomEmbeddings(embedding_model)
        self.vectorstore = None
        self.documents = []
    
    def add_documents(self, texts: List[str], metadatas: List[dict] = None):
        """ドキュメントを追加"""
        if metadatas is None:
            metadatas = [{"source": f"doc_{i}"} for i in range(len(texts))]
        
        documents = [Document(page_content=text, metadata=meta) 
                    for text, meta in zip(texts, metadatas)]
        
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vectorstore.add_documents(documents)
        
        self.documents.extend(documents)
    
    def hybrid_search(self, query: str, k: int = 5, score_threshold: float = 0.5):
        """ハイブリッド検索（セマンティック + キーワード）"""
        # セマンティック検索
        semantic_results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        # キーワード検索（簡単な実装）
        query_words = set(query.lower().split())
        keyword_scores = []
        
        for doc in self.documents:
            doc_words = set(doc.page_content.lower().split())
            overlap = len(query_words.intersection(doc_words))
            score = overlap / len(query_words) if query_words else 0
            keyword_scores.append((doc, score))
        
        # スコアが閾値以上のドキュメントをフィルタ
        filtered_results = [(doc, score) for doc, score in semantic_results 
                          if score >= score_threshold]
        
        return filtered_results
    
    def rerank_results(self, query: str, results: List[tuple], alpha: float = 0.7):
        """結果の再ランキング"""
        query_embedding = torch.tensor(self.embeddings.embed_query(query))
        
        reranked = []
        for doc, original_score in results:
            doc_embedding = torch.tensor(self.embeddings.embed_query(doc.page_content))
            
            # コサイン類似度の計算
            cosine_sim = torch.cosine_similarity(
                query_embedding.unsqueeze(0), 
                doc_embedding.unsqueeze(0)
            ).item()
            
            # スコアの結合
            final_score = alpha * (1 - original_score) + (1 - alpha) * cosine_sim
            reranked.append((doc, final_score))
        
        # スコアでソート
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked

# 使用例
def demo_advanced_rag():
    rag = AdvancedRAGSystem()
    
    # サンプルデータ
    documents = [
        "PyTorchは動的計算グラフを使用する深層学習フレームワークです。",
        "LangChainはLLMアプリケーション開発のためのフレームワークです。",
        "RAGは検索拡張生成と呼ばれ、検索と生成を組み合わせた手法です。",
        "ベクトルデータベースは高次元ベクトルの類似検索に最適化されています。",
        "Transformerアーキテクチャは自然言語処理の主流になっています。"
    ]
    
    rag.add_documents(documents)
    
    query = "PyTorchの特徴について"
    results = rag.hybrid_search(query, k=3)
    reranked = rag.rerank_results(query, results)
    
    print(f"クエリ: {query}")
    print("検索結果:")
    for i, (doc, score) in enumerate(reranked):
        print(f"{i+1}. スコア: {score:.3f}")
        print(f"   内容: {doc.page_content}")
        print()

if __name__ == "__main__":
    demo_advanced_rag()