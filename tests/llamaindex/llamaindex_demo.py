"""
LlamaIndexのDB統合機能を使用したRAGシステムのサンプル
"""

from llamaindex_db_manager import LlamaIndexDBManager
from llama_index.core import Document
from typing import List
import time


# LlamaIndex統合システム設定
LLAMAINDEX_CONFIG = {
    # Ollama設定
    "ollama_url": "http://localhost:11434",
    "llm_model": "llama3.2:3b",
    "embedding_model": "nomic-embed-text",
    
    # Milvus設定 (LlamaIndex Vector Store)
    "milvus_host": "localhost",
    "milvus_port": 19530,
    "milvus_collection": "llamaindex_vectors",
    "embedding_dim": 768,
    
    # MongoDB設定 (LlamaIndex Document Store)
    "mongo_host": "localhost", 
    "mongo_port": 27017,
    "mongo_db": "llamaindex_docs",
    "mongo_namespace": "documents",
    
    # Redis設定 (LlamaIndex KV Store)
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0,
    
    # Neo4j設定 (LlamaIndex Graph Store)
    "neo4j_user": "neo4j",
    "neo4j_password": "password",
    "neo4j_url": "bolt://localhost:7687",
    "neo4j_database": "neo4j",
    
    # テキスト処理設定
    "chunk_size": 1024,
    "chunk_overlap": 20
}


def main():
    """LlamaIndex DB統合機能のデモ"""
    
    print("=== LlamaIndex DB統合RAGシステム ===")
    
    # システム初期化
    manager = LlamaIndexDBManager(LLAMAINDEX_CONFIG)
    
    try:
        # 1. サンプルドキュメントでインデックス作成
        print("\n1. サンプルインデックス作成")
        
        sample_docs = [
            Document(text="機械学習は人工知能の一分野で、データから学習するアルゴリズムを研究します。", 
                    metadata={"topic": "AI", "category": "tech"}),
            Document(text="深層学習はニューラルネットワークを多層化した手法で、画像認識や自然言語処理で優れた性能を発揮します。",
                    metadata={"topic": "Deep Learning", "category": "tech"}),
            Document(text="Python は機械学習とデータサイエンスで最も人気のあるプログラミング言語です。",
                    metadata={"topic": "Programming", "category": "tech"}),
            Document(text="LlamaIndexは様々なデータソースを統合してRAGシステムを構築するためのフレームワークです。",
                    metadata={"topic": "LlamaIndex", "category": "framework"})
        ]
        
        # インデックス作成
        start_time = time.time()
        index = manager.create_index_from_documents(sample_docs, "tech_docs")
        creation_time = time.time() - start_time
        print(f"インデックス作成時間: {creation_time:.2f}秒")
        
        # 2. 高速検索テスト
        print("\n2. 高速ベクトル検索")
        
        search_queries = [
            "機械学習について教えて",
            "Pythonの特徴は？",
            "LlamaIndexとは何ですか"
        ]
        
        for query in search_queries:
            print(f"\nクエリ: {query}")
            start_time = time.time()
            results = manager.search(query, top_k=2, index_name="tech_docs")
            search_time = time.time() - start_time
            
            print(f"検索時間: {search_time:.3f}秒")
            for i, result in enumerate(results, 1):
                print(f"  結果{i}: スコア={result['score']:.3f}")
                print(f"         テキスト: {result['text'][:60]}...")
                print(f"         メタデータ: {result['metadata']}")
        
        # 3. RAG質問応答
        print("\n3. RAG質問応答システム")
        
        rag_questions = [
            "機械学習と深層学習の違いを説明してください",
            "PythonがAI分野で人気な理由は？"
        ]
        
        for question in rag_questions:
            print(f"\n質問: {question}")
            start_time = time.time()
            answer = manager.query_with_rag(question, top_k=3, index_name="tech_docs")
            rag_time = time.time() - start_time
            
            print(f"回答生成時間: {rag_time:.2f}秒")
            print(f"回答: {answer}")
        
        # 4. ディレクトリから一括インデックス作成
        print("\n4. ディレクトリインデックス作成（サンプル）")
        
        # 実際のディレクトリがある場合のみ実行
        # directory_path = "./sample_docs"
        # if Path(directory_path).exists():
        #     start_time = time.time()
        #     dir_index = manager.create_index_from_directory(directory_path, "directory_docs")
        #     dir_creation_time = time.time() - start_time
        #     print(f"ディレクトリインデックス作成時間: {dir_creation_time:.2f}秒")
        # else:
        #     print("サンプルディレクトリが見つかりません")
        
        # 5. インデックス統計情報
        print("\n5. インデックス統計")
        stats = manager.get_index_stats("tech_docs")
        print(f"統計情報: {stats}")
        
        # 6. 利用可能インデックス一覧
        print("\n6. インデックス一覧")
        indexes = manager.list_indexes()
        print(f"利用可能インデックス: {indexes}")
        
        # 7. インデックス追加更新
        print("\n7. インデックス更新")
        
        additional_docs = [
            Document(text="Transformerアーキテクチャは自然言語処理で革命をもたらしました。",
                    metadata={"topic": "Transformer", "category": "tech"}),
            Document(text="RAGシステムは検索強化生成の手法で、外部知識を活用して回答品質を向上させます。",
                    metadata={"topic": "RAG", "category": "tech"})
        ]
        
        success = manager.add_documents_to_index(additional_docs, "tech_docs")
        if success:
            print("ドキュメント追加成功")
            
            # 更新後の検索テスト
            updated_results = manager.search("Transformer", top_k=2, index_name="tech_docs")
            print(f"更新後検索結果数: {len(updated_results)}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    print("\n=== デモ終了 ===")


def performance_test():
    """パフォーマンステスト"""
    
    print("=== パフォーマンステスト ===")
    
    manager = LlamaIndexDBManager(LLAMAINDEX_CONFIG)
    
    # 大量ドキュメントでテスト
    print("大量ドキュメントでのパフォーマンステスト")
    
    # 100個のサンプルドキュメント生成
    large_docs = []
    for i in range(100):
        text = f"これはテストドキュメント {i} です。" * 10  # 長めのテキスト
        doc = Document(text=text, metadata={"doc_id": i, "batch": "performance_test"})
        large_docs.append(doc)
    
    # インデックス作成時間測定
    print(f"ドキュメント数: {len(large_docs)}")
    
    start_time = time.time()
    index = manager.create_index_from_documents(large_docs, "performance_test")
    creation_time = time.time() - start_time
    
    print(f"大量インデックス作成時間: {creation_time:.2f}秒")
    print(f"1ドキュメントあたり: {creation_time/len(large_docs)*1000:.2f}ms")
    
    # 検索パフォーマンステスト
    test_queries = ["テスト", "ドキュメント", "サンプル"]
    
    total_search_time = 0
    for query in test_queries:
        start_time = time.time()
        results = manager.search(query, top_k=10, index_name="performance_test")
        search_time = time.time() - start_time
        total_search_time += search_time
        
        print(f"検索 '{query}': {search_time:.3f}秒, 結果数: {len(results)}")
    
    print(f"平均検索時間: {total_search_time/len(test_queries):.3f}秒")
    
    # クリーンアップ
    manager.delete_index("performance_test")
    print("パフォーマンステスト用インデックスを削除しました")


def interactive_chat():
    """インタラクティブチャット"""
    
    print("=== インタラクティブチャット ===")
    print("'quit'で終了")
    
    manager = LlamaIndexDBManager(LLAMAINDEX_CONFIG)
    
    # サンプルデータでインデックス作成
    sample_docs = [
        Document(text="LlamaIndexは効率的なRAGシステムを構築するためのフレームワークです。"),
        Document(text="Ollama は軽量でローカルで実行可能なLLMサーバーです。"),
        Document(text="Milvusは高性能なベクトルデータベースです。"),
        Document(text="MongoDBはドキュメント指向のNoSQLデータベースです。")
    ]
    
    manager.create_index_from_documents(sample_docs, "chat_docs")
    
    # チャットエンジン作成
    chat_engine = manager.create_chat_engine("chat_docs")
    
    if not chat_engine:
        print("チャットエンジンの作成に失敗しました")
        return
    
    while True:
        try:
            user_input = input("\nあなた: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
            
            # チャット応答
            start_time = time.time()
            response = chat_engine.chat(user_input)
            response_time = time.time() - start_time
            
            print(f"アシスタント ({response_time:.2f}秒): {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"エラー: {e}")
    
    print("チャット終了")


if __name__ == "__main__":
    # メインデモ実行
    main()
    
    # その他のテスト（コメントアウト）
    # performance_test()
    # interactive_chat()