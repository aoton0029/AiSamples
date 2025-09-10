import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from document_service import DocumentService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """メインデモ関数"""
    service = None
    
    try:
        # ドキュメントサービス初期化
        logger.info("=== LlamaIndex Multi-Database Architecture Demo ===")
        logger.info("Initializing document service...")
        
        service = DocumentService()
        success = await service.initialize()
        
        if not success:
            logger.error("Failed to initialize document service")
            return
        
        logger.info("✅ Document service initialized successfully")
        
        # システム統計表示
        await display_system_stats(service)
        
        # サンプルドキュメント作成
        await create_sample_documents(service)
        
        # 検索デモ
        await search_demo(service)
        
        # 関係性デモ
        await relations_demo(service)
        
        # 統計表示
        await display_system_stats(service)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    
    finally:
        if service:
            await service.shutdown()
            logger.info("🔌 Document service shutdown completed")

async def display_system_stats(service: DocumentService):
    """システム統計表示"""
    try:
        logger.info("\n📊 System Statistics:")
        stats = await service.get_system_stats()
        
        # MongoDB統計
        if "mongodb" in stats and stats["mongodb"]:
            mongo_stats = stats["mongodb"]
            logger.info(f"  📄 MongoDB: {mongo_stats.get('total_documents', 0)} documents")
            file_types = mongo_stats.get('file_type_distribution', {})
            for file_type, count in file_types.items():
                logger.info(f"    - {file_type}: {count}")
        
        # Milvus統計
        if "milvus" in stats and stats["milvus"]:
            milvus_stats = stats["milvus"]
            logger.info(f"  🔍 Milvus: {milvus_stats.get('total_entities', 0)} vectors")
        
        # Neo4j統計
        if "neo4j" in stats and stats["neo4j"]:
            neo4j_stats = stats["neo4j"]
            logger.info(f"  🕸️  Neo4j: {neo4j_stats.get('total_nodes', 0)} nodes, {neo4j_stats.get('total_relationships', 0)} relationships")
            rel_types = neo4j_stats.get('relationship_types', {})
            for rel_type, count in rel_types.items():
                logger.info(f"    - {rel_type}: {count}")
        
        # Redis統計
        if "redis" in stats and stats["redis"]:
            redis_stats = stats["redis"]
            logger.info(f"  💾 Redis: {redis_stats.get('total_keys', 0)} keys, {redis_stats.get('memory_used', 'N/A')} memory")
        
        logger.info("")
        
    except Exception as e:
        logger.error(f"Failed to display stats: {e}")

async def create_sample_documents(service: DocumentService):
    """サンプルドキュメント作成"""
    try:
        logger.info("📝 Creating sample documents...")
        
        # サンプルテキストファイル作成
        sample_files = [
            {
                "filename": "ai_overview.txt",
                "content": """人工知能（AI）は、機械学習、深層学習、自然言語処理などの技術を組み合わせた革新的な分野です。
                
機械学習では、データからパターンを学習し、予測や分類を行います。代表的な手法には教師あり学習、教師なし学習、強化学習があります。

深層学習は、ニューラルネットワークを多層化したアプローチで、画像認識、音声認識、自然言語処理で優れた性能を示しています。

自然言語処理（NLP）は、人間の言語をコンピュータが理解・処理する技術で、機械翻訳、文書要約、質問応答システムなどに応用されています。

近年では、Transformer、BERT、GPTなどの大規模言語モデルが注目を集めており、ChatGPTなどの対話AIが広く普及しています。""",
                "metadata": {"category": "technology", "topic": "artificial_intelligence"}
            },
            {
                "filename": "machine_learning.txt",
                "content": """機械学習は人工知能の重要な分野で、アルゴリズムがデータから自動的に学習する技術です。

主要な学習タイプ：
1. 教師あり学習 - ラベル付きデータから学習（分類、回帰）
2. 教師なし学習 - ラベルなしデータからパターン発見（クラスタリング、次元削減）
3. 強化学習 - 環境との相互作用を通じて最適な行動を学習

代表的なアルゴリズム：
- 線形回帰、ロジスティック回帰
- 決定木、ランダムフォレスト
- サポートベクターマシン（SVM）
- k-means、DBSCAN
- ニューラルネットワーク

機械学習は、推薦システム、画像認識、自動運転、医療診断、金融分析など様々な分野で活用されています。""",
                "metadata": {"category": "technology", "topic": "machine_learning"}
            },
            {
                "filename": "database_systems.txt",
                "content": """データベースシステムは、大量のデータを効率的に格納、管理、検索するためのソフトウェアです。

主要なデータベースタイプ：

1. リレーショナルデータベース（RDBMS）
   - MySQL、PostgreSQL、Oracle、SQL Server
   - ACID特性、SQL言語、正規化

2. NoSQLデータベース
   - ドキュメント型：MongoDB、CouchDB
   - キー・バリュー型：Redis、DynamoDB
   - カラム型：Cassandra、HBase
   - グラフ型：Neo4j、Amazon Neptune

3. ベクトルデータベース
   - Milvus、Pinecone、Weaviate
   - 機械学習、セマンティック検索に特化

4. インメモリデータベース
   - Redis、Memcached
   - 高速アクセス、キャッシング

データベース設計では、データの整合性、パフォーマンス、スケーラビリティ、セキュリティを考慮する必要があります。""",
                "metadata": {"category": "technology", "topic": "databases"}
            }
        ]
        
        # ファイル作成と処理
        for file_info in sample_files:
            file_path = project_root / file_info["filename"]
            
            # ファイル作成
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info["content"])
            
            # ドキュメント処理
            document_id = await service.process_file(str(file_path), file_info["metadata"])
            
            if document_id:
                logger.info(f"  ✅ Created: {file_info['filename']} (ID: {document_id[:8]}...)")
            else:
                logger.error(f"  ❌ Failed: {file_info['filename']}")
            
            # ファイル削除（クリーンアップ）
            if file_path.exists():
                file_path.unlink()
        
        logger.info("📝 Sample documents created successfully\n")
        
    except Exception as e:
        logger.error(f"Failed to create sample documents: {e}")

async def search_demo(service: DocumentService):
    """検索デモ"""
    try:
        logger.info("🔍 Search Demo:")
        
        search_queries = [
            "機械学習のアルゴリズム",
            "データベースの種類",
            "ニューラルネットワーク",
            "NoSQL database",
            "人工知能の応用"
        ]
        
        for query in search_queries:
            logger.info(f"\n  Query: '{query}'")
            
            # ハイブリッド検索
            results = await service.search_documents(query, search_type="hybrid", limit=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"    {i}. {result.document_title} (Score: {result.score:.3f})")
                    logger.info(f"       {result.content[:100]}...")
            else:
                logger.info("    No results found")
        
        logger.info("\n🔍 Search demo completed\n")
        
    except Exception as e:
        logger.error(f"Search demo failed: {e}")

async def relations_demo(service: DocumentService):
    """関係性デモ"""
    try:
        logger.info("🕸️  Document Relations Demo:")
        
        # 全ドキュメント取得
        all_docs = await service.mongo_repo.search_documents({"limit": 10})
        
        if len(all_docs) < 2:
            logger.info("  Not enough documents for relation demo")
            return
        
        # 各ドキュメントの関連性確認
        for doc in all_docs[:3]:  # 最初の3つのドキュメント
            logger.info(f"\n  Document: {doc.title}")
            
            related_ids = await service.get_related_documents(doc.id)
            
            if related_ids:
                logger.info(f"    Related documents ({len(related_ids)}):")
                
                # 関連ドキュメントの詳細取得
                related_docs = await service.mongo_repo.get_documents_by_ids(related_ids[:3])
                for related_doc in related_docs:
                    logger.info(f"      - {related_doc.title}")
            else:
                logger.info("    No related documents found")
        
        logger.info("\n🕸️  Relations demo completed\n")
        
    except Exception as e:
        logger.error(f"Relations demo failed: {e}")

async def health_check_demo(service: DocumentService):
    """ヘルスチェックデモ"""
    try:
        logger.info("🏥 Health Check Demo:")
        
        health_checks = [
            ("MongoDB", service.mongo_repo.health_check()),
            ("Milvus", service.milvus_repo.health_check()),
            ("Neo4j", service.neo4j_repo.health_check()),
            ("Redis", service.redis_repo.health_check()),
            ("Ollama", service.ollama_client.health_check())
        ]
        
        results = await asyncio.gather(*[check[1] for check in health_checks], return_exceptions=True)
        
        for i, (service_name, _) in enumerate(health_checks):
            status = "✅ Healthy" if results[i] is True else "❌ Unhealthy"
            logger.info(f"  {service_name}: {status}")
        
        logger.info("\n🏥 Health check completed\n")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        sys.exit(1)