from db.database import get_db, DBType, db_manager
from pdf_vectorize_sample.pdf_vectorizer import PDFVectorizerSQLServer2025
from pdf_vectorize_sample.models import Base

def setup_database():
    """データベースセットアップ"""
    # テーブルとベクトルインデックスを作成
    db_manager.create_tables(DBType.SQLSERVER)

def main():
    # データベースセットアップ
    setup_database()
    
    # ベクトル化処理（384次元のモデルを使用）
    vectorizer = PDFVectorizerSQLServer2025(
        chunk_size=800,
        chunk_overlap=100,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # 384次元
    )
    
    with get_db(DBType.SQLSERVER) as db:
        # PDFを処理してSQL Server 2025に保存
        pdf_files = ["sample1.pdf", "sample2.pdf"]
        
        for pdf_file in pdf_files:
            try:
                document = vectorizer.process_pdf(pdf_file, db)
                print(f"✓ Processed: {document.filename} (ID: {document.id})")
            except Exception as e:
                print(f"✗ Failed to process {pdf_file}: {str(e)}")
        
        # 統計情報表示
        stats = vectorizer.get_document_stats(db)
        print("\n=== Database Statistics ===")
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Total Chunks: {stats['total_chunks']}")
        print(f"Total Vectors: {stats['total_vectors']}")
        print(f"Average Chunk Size: {stats['avg_chunk_size']:.1f} characters")
        print(f"Total Pages: {stats['total_pages']}")
        
        # ベクトル検索のテスト
        queries = [
            "機械学習について",
            "データベースの設計",
            "プログラミング言語"
        ]
        
        print("\n=== Vector Search Results ===")
        for query in queries:
            print(f"\nQuery: '{query}'")
            results = vectorizer.search_similar_chunks_vector(
                query, db, top_k=3, similarity_threshold=0.6
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['filename']} (Page {result['page_number']})")
                    print(f"     Similarity: {result['similarity']:.4f}")
                    print(f"     Content: {result['content'][:100]}...")
            else:
                print("  No similar content found.")
