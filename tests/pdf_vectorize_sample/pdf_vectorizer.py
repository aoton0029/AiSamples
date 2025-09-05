import os
import numpy as np
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument

from db.database import get_db, DBType
from pdf_vectorize_sample.models import Document, DocumentChunk, DocumentVector

class PDFVectorizerSQLServer2025:
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.embedding_model = embedding_model
        self.vector_dimension = self._get_vector_dimension()
    
    def _get_vector_dimension(self) -> int:
        """埋め込みモデルのベクトル次元を取得"""
        test_vector = self.embeddings.embed_query("test")
        return len(test_vector)
    
    def check_document_exists(self, pdf_path: str, db: Session) -> Optional[Document]:
        """ファイルが既に処理済みかチェック"""
        file_hash = Document.calculate_file_hash(pdf_path)
        return db.query(Document).filter(Document.file_hash == file_hash).first()
    
    def process_pdf(self, pdf_path: str, db: Session, force_reprocess: bool = False) -> Document:
        """PDFを処理してSQL Server 2025に保存"""
        
        # 既存チェック
        if not force_reprocess:
            existing_doc = self.check_document_exists(pdf_path, db)
            if existing_doc:
                print(f"Document {existing_doc.filename} already exists (ID: {existing_doc.id})")
                return existing_doc
        
        # 1. PDFファイル情報をデータベースに保存
        filename = os.path.basename(pdf_path)
        file_hash = Document.calculate_file_hash(pdf_path)
        
        document = Document(
            filename=filename,
            file_path=pdf_path,
            file_hash=file_hash
        )
        db.add(document)
        db.flush()
        
        try:
            # 2. PDFからドキュメントをロード
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            document.total_pages = len(pages)
            
            print(f"Processing {len(pages)} pages from {filename}")
            
            # 3. テキストを分割してチャンクを作成
            chunks = self.text_splitter.split_documents(pages)
            print(f"Created {len(chunks)} chunks")
            
            # 4. バッチでベクトル化（効率化）
            chunk_texts = [chunk.page_content for chunk in chunks]
            vectors = self.embeddings.embed_documents(chunk_texts)
            
            # 5. 各チャンクとベクトルを保存
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                # チャンク情報をデータベースに保存
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk.page_content,
                    page_number=chunk.metadata.get('page', None),
                    chunk_size=len(chunk.page_content)
                )
                db.add(doc_chunk)
                db.flush()
                
                # ベクトルをSQL Server 2025のVECTOR型で保存
                doc_vector = DocumentVector(
                    chunk_id=doc_chunk.id,
                    vector_embedding=vector,  # ベクトル型として直接保存
                    embedding_model=self.embedding_model
                )
                db.add(doc_vector)
                
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(chunks)} chunks")
            
            db.commit()
            print(f"Successfully processed and saved {filename}")
            return document
            
        except Exception as e:
            db.rollback()
            print(f"Error processing {filename}: {str(e)}")
            raise
    
    def search_similar_chunks_vector(self, 
                                   query: str, 
                                   db: Session, 
                                   top_k: int = 5,
                                   similarity_threshold: float = 0.7) -> List[dict]:
        """SQL Server 2025のベクトル検索を使用した類似チャンク検索"""
        
        # クエリをベクトル化
        query_vector = self.embeddings.embed_query(query)
        
        # SQL Server 2025のベクトル検索構文を使用
        sql_query = text("""
            SELECT TOP :top_k
                dc.id as chunk_id,
                dc.content,
                dc.page_number,
                d.filename,
                dv.vector_embedding.COSINE_DISTANCE(:query_vector) as distance,
                (1 - dv.vector_embedding.COSINE_DISTANCE(:query_vector)) as similarity
            FROM document_vectors dv
            INNER JOIN document_chunks dc ON dv.chunk_id = dc.id
            INNER JOIN documents d ON dc.document_id = d.id
            WHERE dv.embedding_model = :model_name
            AND (1 - dv.vector_embedding.COSINE_DISTANCE(:query_vector)) >= :threshold
            ORDER BY dv.vector_embedding.COSINE_DISTANCE(:query_vector) ASC
        """)
        
        result = db.execute(sql_query, {
            'top_k': top_k,
            'query_vector': query_vector,
            'model_name': self.embedding_model,
            'threshold': similarity_threshold
        })
        
        results = []
        for row in result:
            results.append({
                'chunk_id': row.chunk_id,
                'content': row.content,
                'filename': row.filename,
                'page_number': row.page_number,
                'distance': float(row.distance),
                'similarity': float(row.similarity)
            })
        
        return results
    
    def get_document_stats(self, db: Session) -> dict:
        """ドキュメント統計情報を取得"""
        stats = db.execute(text("""
            SELECT 
                COUNT(DISTINCT d.id) as total_documents,
                COUNT(DISTINCT dc.id) as total_chunks,
                COUNT(DISTINCT dv.id) as total_vectors,
                AVG(CAST(dc.chunk_size AS FLOAT)) as avg_chunk_size,
                SUM(d.total_pages) as total_pages
            FROM documents d
            LEFT JOIN document_chunks dc ON d.id = dc.document_id
            LEFT JOIN document_vectors dv ON dc.id = dv.chunk_id
        """)).fetchone()
        
        return {
            'total_documents': stats.total_documents or 0,
            'total_chunks': stats.total_chunks or 0,
            'total_vectors': stats.total_vectors or 0,
            'avg_chunk_size': float(stats.avg_chunk_size or 0),
            'total_pages': stats.total_pages or 0
        }