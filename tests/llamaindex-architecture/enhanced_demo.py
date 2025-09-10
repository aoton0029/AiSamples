import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from enhanced_document_service import EnhancedDocumentService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """拡張機能デモ"""
    service = None
    
    try:
        logger.info("=== Enhanced LlamaIndex Multi-Database Architecture Demo ===")
        logger.info("Initializing enhanced document service...")
        
        service = EnhancedDocumentService()
        success = await service.initialize()
        
        if not success:
            logger.error("Failed to initialize enhanced document service")
            return
        
        logger.info("✅ Enhanced document service initialized successfully")
        
        # 拡張システム統計表示
        await display_enhanced_stats(service)
        
        # 拡張サンプルドキュメント作成
        await create_enhanced_sample_documents(service)
        
        # 知的検索デモ
        await intelligent_search_demo(service)
        
        # 自然言語クエリデモ
        await natural_language_query_demo(service)
        
        # パフォーマンス統計
        await performance_analysis_demo(service)
        
        # 最終統計表示
        await display_enhanced_stats(service)
        
    except Exception as e:
        logger.error(f"Enhanced demo failed: {e}")
    
    finally:
        if service:
            await service.shutdown()
            logger.info("🔌 Enhanced document service shutdown completed")

async def display_enhanced_stats(service: EnhancedDocumentService):
    """拡張システム統計表示"""
    try:
        logger.info("\n📊 Enhanced System Statistics:")
        stats = await service.get_enhanced_system_stats()
        
        # 基本統計
        if "mongodb" in stats and stats["mongodb"]:
            mongo_stats = stats["mongodb"]
            logger.info(f"  📄 MongoDB: {mongo_stats.get('total_documents', 0)} documents")
        
        if "milvus" in stats and stats["milvus"]:
            milvus_stats = stats["milvus"]
            logger.info(f"  🔍 Milvus: Vector store ready - {milvus_stats.get('status', 'unknown')}")
        
        # Neo4j拡張統計
        if "neo4j_enhanced" in stats and stats["neo4j_enhanced"]:
            neo4j_stats = stats["neo4j_enhanced"]
            logger.info(f"  🕸️  Neo4j Enhanced:")
            logger.info(f"    - Documents: {neo4j_stats.get('total_documents', 0)}")
            logger.info(f"    - Tags: {neo4j_stats.get('total_tags', 0)}")
            logger.info(f"    - Relationships: {neo4j_stats.get('total_relationships', 0)}")
        
        # Ollama性能統計
        if "ollama_performance" in stats and stats["ollama_performance"]:
            ollama_stats = stats["ollama_performance"]
            logger.info(f"  🤖 Ollama Performance:")
            logger.info(f"    - Embeddings generated: {ollama_stats.get('embeddings_generated', 0)}")
            logger.info(f"    - Cache hit ratio: {ollama_stats.get('cache_hit_ratio', 0):.2%}")
            logger.info(f"    - Cache size: {ollama_stats.get('cache_size', 0)}")
        
        # LlamaIndex状態
        if "llamaindex_status" in stats and stats["llamaindex_status"]:
            li_stats = stats["llamaindex_status"]
            logger.info(f"  🦙 LlamaIndex Status:")
            logger.info(f"    - Vector Index: {'✅' if li_stats.get('vector_index_ready') else '❌'}")
            logger.info(f"    - Query Engine: {'✅' if li_stats.get('query_engine_ready') else '❌'}")
            logger.info(f"    - Retriever: {'✅' if li_stats.get('retriever_ready') else '❌'}")
        
        logger.info("")
        
    except Exception as e:
        logger.error(f"Failed to display enhanced stats: {e}")

async def create_enhanced_sample_documents(service: EnhancedDocumentService):
    """拡張サンプルドキュメント作成"""
    try:
        logger.info("📝 Creating enhanced sample documents...")
        
        # より詳細なサンプルファイル
        enhanced_sample_files = [
            {
                "filename": "advanced_ai_research.txt",
                "content": """最新の人工知能研究動向

近年の人工知能（AI）研究は驚異的な進歩を遂げています。特に大規模言語モデル（LLM）の発展により、自然言語処理、機械翻訳、文書生成、コード生成などの分野で革新的な成果が生まれています。

主要な研究分野：

1. トランスフォーマーアーキテクチャ
Attention機構を基盤とするTransformerは、BERT、GPT、T5などのモデルの基礎となっています。自己注意機構により、長距離の依存関係を効率的にモデル化できます。

2. マルチモーダルAI
CLIP、DALL-E、GPT-4のように、テキスト、画像、音声を統合的に処理するマルチモーダルAIが注目されています。これにより、より人間に近い理解と生成が可能になります。

3. 強化学習との融合
ChatGPTで用いられたRLHF（Reinforcement Learning from Human Feedback）のように、強化学習を用いてAIの出力を人間の価値観に合わせる研究が進んでいます。

4. 効率化技術
大規模モデルの計算コストを削減するため、蒸留、プルーニング、量子化、LoRAなどの効率化技術が開発されています。

今後の展望：
- AGI（Artificial General Intelligence）に向けた研究
- 説明可能AI（XAI）の発展
- エッジデバイスでのAI実行
- AI倫理とガバナンスの確立

これらの技術は、医療、教育、エンターテインメント、製造業など、あらゆる分野での応用が期待されています。""",
                "metadata": {
                    "category": "research", 
                    "topic": "artificial_intelligence",
                    "research_level": "advanced",
                    "publication_year": 2024
                }
            },
            {
                "filename": "quantum_computing_basics.txt",
                "content": """量子コンピューティング入門

量子コンピューティングは、量子力学の原理を利用した革新的な計算技術です。従来のコンピュータとは根本的に異なる原理で動作し、特定の問題に対して指数的な高速化を実現できる可能性があります。

基本概念：

1. 量子ビット（Qubit）
従来のビットは0または1の状態をとりますが、量子ビットは0と1の重ね合わせ状態を持てます。これにより、n個の量子ビットで2^n個の状態を同時に表現できます。

2. 量子もつれ（Entanglement）
複数の量子ビット間に強い相関関係が生まれる現象です。一方の量子ビットの状態を測定すると、瞬時に他方の状態が決まります。

3. 量子干渉（Interference）
量子状態の振幅が干渉し合うことで、正しい答えの確率を高め、間違った答えの確率を低くします。

主要なアルゴリズム：
- Shorのアルゴリズム: 素因数分解を効率的に実行
- Groverのアルゴリズム: データベース検索を高速化
- VQE（Variational Quantum Eigensolver）: 分子シミュレーション

応用分野：
- 暗号解読とセキュリティ
- 薬物発見と分子シミュレーション
- 最適化問題
- 機械学習の高速化

現在の課題：
- 量子デコヒーレンス（ノイズ）
- エラー修正技術
- スケーラビリティ
- 量子ソフトウェア開発

IBM、Google、Microsoft、Amazonなどの企業が量子コンピュータの実用化に向けて競争しており、NISQ（Noisy Intermediate-Scale Quantum）時代から本格的な量子優位性の実現へと進んでいます。""",
                "metadata": {
                    "category": "technology", 
                    "topic": "quantum_computing",
                    "difficulty": "intermediate",
                    "target_audience": "engineers"
                }
            },
            {
                "filename": "sustainable_technology.txt",
                "content": """持続可能な技術革新

気候変動とエネルギー危機への対応として、持続可能な技術革新が急務となっています。テクノロジー業界も環境負荷を削減し、循環型社会の実現に向けた取り組みを加速させています。

主要な技術分野：

1. 再生可能エネルギー技術
- 太陽光発電の効率向上（ペロブスカイト太陽電池、タンデム型セル）
- 風力発電の大型化と洋上展開
- 地熱、潮力、バイオマスエネルギーの活用
- エネルギー貯蔵技術（リチウムイオン電池、固体電池、水素燃料電池）

2. グリーンコンピューティング
- 省電力プロセッサの開発
- データセンターの冷却効率化
- クラウドサービスの最適化
- AIを活用したエネルギー管理

3. サーキュラーエコノミー
- リサイクル技術の向上
- バイオベース材料の開発
- 製品ライフサイクル管理
- シェアリングエコノミープラットフォーム

4. カーボンニュートラル技術
- 炭素回収・利用・貯留（CCUS）
- 直接空気回収（DAC）
- メタネーション技術
- グリーン水素製造

デジタル技術の活用：
- IoTによる環境モニタリング
- AIを活用した最適化
- ブロックチェーンによる透明性確保
- デジタルツインによるシミュレーション

企業の取り組み：
- RE100（再生可能エネルギー100%）への参加
- カーボンニュートラル宣言
- ESG投資の拡大
- サプライチェーンの透明化

政策的支援：
- グリーンニューディール政策
- カーボンプライシング
- 技術開発への補助金
- 国際協力の推進

持続可能な技術革新は、環境保護と経済成長の両立を可能にし、次世代への責任を果たす鍵となります。技術者、企業、政府が連携して、より良い未来を築いていく必要があります。""",
                "metadata": {
                    "category": "sustainability", 
                    "topic": "green_technology",
                    "impact": "global",
                    "urgency": "high"
                }
            }
        ]
        
        # ファイル作成と拡張処理
        for file_info in enhanced_sample_files:
            file_path = project_root / file_info["filename"]
            
            # ファイル作成
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info["content"])
            
            # 拡張ドキュメント処理
            document_id = await service.process_file_enhanced(
                str(file_path), 
                file_info["metadata"],
                extract_entities=True,
                analyze_sentiment=True
            )
            
            if document_id:
                logger.info(f"  ✅ Enhanced: {file_info['filename']} (ID: {document_id[:8]}...)")
            else:
                logger.error(f"  ❌ Failed: {file_info['filename']}")
            
            # ファイル削除（クリーンアップ）
            if file_path.exists():
                file_path.unlink()
        
        logger.info("📝 Enhanced sample documents created successfully\n")
        
    except Exception as e:
        logger.error(f"Failed to create enhanced sample documents: {e}")

async def intelligent_search_demo(service: EnhancedDocumentService):
    """知的検索デモ"""
    try:
        logger.info("🧠 Intelligent Search Demo:")
        
        enhanced_queries = [
            "量子コンピュータの基本原理とアルゴリズム",
            "AI研究における最新のトランスフォーマー技術",
            "持続可能なエネルギー技術の発展",
            "機械学習と強化学習の融合",
            "環境技術とデジタル革新"
        ]
        
        for query in enhanced_queries:
            logger.info(f"\n  🔍 Intelligent Query: '{query}'")
            
            # 知的検索実行
            results = await service.intelligent_search(
                query, 
                search_type="hybrid", 
                include_metadata=True,
                rerank=True,
                limit=3
            )
            
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"    {i}. {result.document_title} (Score: {result.score:.3f})")
                    logger.info(f"       {result.content[:120]}...")
                    if result.metadata.get("entities"):
                        entities = result.metadata["entities"][:2]  # 最初の2つのエンティティ
                        entity_names = [e.get("name", "") for e in entities]
                        logger.info(f"       Entities: {', '.join(entity_names)}")
            else:
                logger.info("    No results found")
        
        logger.info("\n🧠 Intelligent search demo completed\n")
        
    except Exception as e:
        logger.error(f"Intelligent search demo failed: {e}")

async def natural_language_query_demo(service: EnhancedDocumentService):
    """自然言語クエリデモ"""
    try:
        logger.info("💬 Natural Language Query Demo:")
        
        nl_questions = [
            "AIと量子コンピューティングの関係について教えてください",
            "持続可能な技術にはどのような種類がありますか？",
            "機械学習の最新トレンドは何ですか？"
        ]
        
        for question in nl_questions:
            logger.info(f"\n  ❓ Question: '{question}'")
            
            # 自然言語クエリ実行
            response = await service.natural_language_query(question)
            
            logger.info(f"  💡 Answer: {response.get('answer', 'No answer available')[:200]}...")
            logger.info(f"  📊 Confidence: {response.get('confidence', 0.0):.2%}")
            logger.info(f"  📚 Sources: {len(response.get('sources', []))} documents")
        
        logger.info("\n💬 Natural language query demo completed\n")
        
    except Exception as e:
        logger.error(f"Natural language query demo failed: {e}")

async def performance_analysis_demo(service: EnhancedDocumentService):
    """パフォーマンス分析デモ"""
    try:
        logger.info("⚡ Performance Analysis Demo:")
        
        # Ollama統計取得
        from ollama_client import ollama_client
        perf_stats = await ollama_client.get_performance_stats()
        
        logger.info(f"  🤖 Ollama Performance:")
        logger.info(f"    - Total embeddings: {perf_stats.get('embeddings_generated', 0)}")
        logger.info(f"    - Total text generations: {perf_stats.get('text_generated', 0)}")
        logger.info(f"    - Cache hits: {perf_stats.get('cache_hits', 0)}")
        logger.info(f"    - Cache misses: {perf_stats.get('cache_misses', 0)}")
        logger.info(f"    - Hit ratio: {perf_stats.get('cache_hit_ratio', 0):.2%}")
        
        # キャッシュクリアテスト
        logger.info("\n  🧹 Testing cache clear...")
        await ollama_client.clear_cache()
        logger.info("  ✅ Cache cleared successfully")
        
        logger.info("\n⚡ Performance analysis completed\n")
        
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Enhanced demo interrupted by user")
    except Exception as e:
        logger.error(f"Enhanced demo failed: {e}")
        sys.exit(1)