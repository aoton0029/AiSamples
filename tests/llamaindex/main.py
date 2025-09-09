"""
RAGシステム用の設定とサンプル使用例
"""

from index_manager import IndexManager
from typing import Dict, Any


# システム設定
CONFIG = {
    # Ollama設定
    "ollama_url": "http://localhost:11434",
    "llm_model": "llama3.2:3b",
    "embedding_model": "nomic-embed-text",
    
    # MongoDB設定
    "mongo_url": "mongodb://localhost:27017",
    "mongo_db": "rag_system",
    
    # Milvus設定
    "milvus_host": "localhost",
    "milvus_port": "19530",
    "milvus_collection": "document_vectors",
    
    # Neo4j設定
    "neo4j_uri": "bolt://localhost:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "password",
    
    # Redis設定
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0,
    
    # テキスト処理設定
    "chunk_size": 1024,
    "chunk_overlap": 20,
    "embedding_dim": 768
}


def main():
    """サンプル使用例"""
    
    # インデックスマネージャーを初期化
    manager = IndexManager(CONFIG)
    
    print("=== RAGシステム開始 ===")
    
    # システム状態確認
    stats = manager.get_system_stats()
    print(f"システム統計: {stats}")
    
    try:
        # 1. ドキュメント追加例
        print("\n1. ドキュメント追加")
        
        # 単一ファイル追加
        # document_id = manager.add_document(
        #     file_path="./documents/sample.pdf",
        #     metadata={"category": "research", "author": "test"}
        # )
        # print(f"追加されたドキュメントID: {document_id}")
        
        # ディレクトリ一括追加
        # document_ids = manager.add_directory(
        #     directory_path="./documents",
        #     metadata={"batch": "2024-01"}
        # )
        # print(f"追加されたドキュメント数: {len(document_ids)}")
        
        # 2. 類似検索例
        print("\n2. 類似検索")
        query = "機械学習について教えて"
        results = manager.search_similar(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"結果 {i}:")
            print(f"  ドキュメントID: {result['document_id']}")
            print(f"  スコア: {result['score']:.4f}")
            print(f"  テキスト: {result['text'][:100]}...")
            print(f"  メタデータ: {result['metadata']}")
            print()
        
        # 3. RAG質問応答例
        print("\n3. RAG質問応答")
        question = "AIの未来について説明してください"
        answer = manager.query_with_rag(question)
        print(f"質問: {question}")
        print(f"回答: {answer}")
        
        # 4. メタデータフィルタリング検索
        print("\n4. フィルタリング検索")
        filtered_results = manager.search_similar(
            query="深層学習",
            top_k=5,
            filter_metadata={"category": "research"}
        )
        print(f"フィルタリング結果数: {len(filtered_results)}")
        
        # 5. 関連ドキュメント検索 (Neo4j)
        print("\n5. 関連ドキュメント検索")
        if results:
            doc_id = results[0]["document_id"]
            related_docs = manager.find_related_documents(doc_id)
            print(f"関連ドキュメント数: {len(related_docs)}")
            for doc in related_docs:
                print(f"  - {doc}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    finally:
        # 接続を閉じる
        manager.close_connections()
        print("\n=== RAGシステム終了 ===")


def batch_processing_example():
    """バッチ処理の例"""
    manager = IndexManager(CONFIG)
    
    # 大量ドキュメントの処理例
    documents_to_process = [
        {"path": "./docs/doc1.pdf", "metadata": {"type": "manual"}},
        {"path": "./docs/doc2.txt", "metadata": {"type": "article"}},
        {"path": "./docs/doc3.docx", "metadata": {"type": "report"}},
    ]
    
    processed_ids = []
    
    for doc_info in documents_to_process:
        try:
            doc_id = manager.add_document(
                doc_info["path"], 
                doc_info["metadata"]
            )
            processed_ids.append(doc_id)
            print(f"処理完了: {doc_info['path']} -> {doc_id}")
        
        except Exception as e:
            print(f"処理失敗: {doc_info['path']} - {e}")
    
    print(f"バッチ処理完了: {len(processed_ids)}件")
    manager.close_connections()
    
    return processed_ids


def search_and_chat_example():
    """検索とチャットの例"""
    manager = IndexManager(CONFIG)
    
    print("=== インタラクティブ検索 ===")
    print("終了するには 'quit' を入力してください")
    
    while True:
        try:
            user_query = input("\n質問を入力してください: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_query:
                continue
            
            # RAG回答を取得
            print("回答を生成中...")
            answer = manager.query_with_rag(user_query, top_k=3)
            
            print(f"\n回答: {answer}")
            
            # 関連する検索結果も表示
            search_results = manager.search_similar(user_query, top_k=2)
            
            if search_results:
                print(f"\n参考ドキュメント:")
                for i, result in enumerate(search_results, 1):
                    print(f"{i}. スコア: {result['score']:.3f}")
                    print(f"   テキスト: {result['text'][:150]}...")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"エラー: {e}")
    
    manager.close_connections()
    print("チャット終了")


if __name__ == "__main__":
    # メイン実行
    main()
    
    # その他の使用例（コメントアウト）
    # batch_processing_example()
    # search_and_chat_example()