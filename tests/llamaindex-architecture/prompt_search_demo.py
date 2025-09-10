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
    """プロンプト検索デモ"""
    service = None
    
    try:
        logger.info("=== Prompt-Based Document Search Demo ===")
        
        # サービス初期化
        service = EnhancedDocumentService()
        success = await service.initialize()
        
        if not success:
            logger.error("Failed to initialize service")
            return
        
        logger.info("✅ Service initialized successfully")
        
        # サンプルドキュメント作成（検索用）
        await create_search_sample_documents(service)
        
        # プロンプト検索デモ実行
        await prompt_search_demo(service)
        
        # 類似ドキュメント検索デモ
        await similar_documents_demo(service)
        
        # 多様なプロンプトテスト
        await diverse_prompt_test(service)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
    
    finally:
        if service:
            await service.shutdown()
            logger.info("🔌 Service shutdown completed")

async def create_search_sample_documents(service: EnhancedDocumentService):
    """検索用サンプルドキュメント作成"""
    try:
        logger.info("📝 Creating search sample documents...")
        
        search_samples = [
            {
                "filename": "python_programming.txt",
                "content": """Pythonプログラミング入門

Pythonは、シンプルで読みやすい構文を持つプログラミング言語です。データサイエンス、ウェブ開発、自動化スクリプトなど幅広い用途で使用されています。

基本的な特徴：
- インタープリター言語
- オブジェクト指向プログラミング
- 豊富なライブラリとフレームワーク
- クロスプラットフォーム対応

主要なライブラリ：
- NumPy: 数値計算
- Pandas: データ分析
- Matplotlib: データ可視化
- Django/Flask: ウェブフレームワーク
- TensorFlow/PyTorch: 機械学習

Pythonは初心者にも学びやすく、プロフェッショナルな開発にも適した言語として人気があります。""",
                "metadata": {"category": "programming", "language": "python", "level": "beginner"}
            },
            {
                "filename": "machine_learning_algorithms.txt",
                "content": """機械学習アルゴリズム概論

機械学習には様々なアルゴリズムがあり、問題の種類や データの性質に応じて選択する必要があります。

教師あり学習：
- 線形回帰: 連続値の予測
- ロジスティック回帰: 分類問題
- 決定木: 解釈しやすいモデル
- ランダムフォレスト: アンサンブル学習
- サポートベクターマシン: 高次元データに効果的
- ニューラルネットワーク: 複雑なパターン学習

教師なし学習：
- k-means: クラスタリング
- 主成分分析(PCA): 次元削減
- DBSCAN: 密度ベースクラスタリング

深層学習：
- CNN: 画像認識
- RNN/LSTM: 時系列データ
- Transformer: 自然言語処理

アルゴリズム選択は、データの性質、問題の複雑さ、解釈可能性の要求などを考慮して決定します。""",
                "metadata": {"category": "ai", "topic": "machine_learning", "level": "intermediate"}
            },
            {
                "filename": "web_development_technologies.txt",
                "content": """ウェブ開発技術スタック

現代のウェブ開発は、フロントエンド、バックエンド、データベースなど様々な技術の組み合わせで構成されています。

フロントエンド技術：
- HTML5: マークアップ言語
- CSS3: スタイリング、アニメーション
- JavaScript: インタラクティブな機能
- React: コンポーネントベースのライブラリ
- Vue.js: プログレッシブフレームワーク
- Angular: 包括的なフレームワーク

バックエンド技術：
- Node.js: JavaScript実行環境
- Python (Django/Flask): 高生産性
- Java (Spring): エンタープライズ開発
- PHP: ウェブ特化言語
- Ruby on Rails: 規約による開発

データベース：
- MySQL: リレーショナルデータベース
- PostgreSQL: 高機能RDB
- MongoDB: ドキュメント型NoSQL
- Redis: インメモリストア

クラウドサービス：
- AWS, Azure, GCP
- Docker, Kubernetes
- CI/CD パイプライン

モダンな開発では、マイクロサービス、API-first設計、レスポンシブデザインが重要です。""",
                "metadata": {"category": "web_development", "stack": "full_stack", "level": "intermediate"}
            },
            {
                "filename": "data_science_workflow.txt",
                "content": """データサイエンスワークフロー

データサイエンスプロジェクトは、明確なワークフローに従って進めることで効率的に価値を創出できます。

1. 問題定義・ゴール設定
- ビジネス課題の明確化
- 成功指標の定義
- プロジェクトスコープの設定

2. データ収集・理解
- データソースの特定
- データ品質の評価
- 探索的データ分析(EDA)

3. データ前処理
- 欠損値処理
- 外れ値検出・処理
- 特徴量エンジニアリング
- データ正規化・標準化

4. モデリング
- アルゴリズム選択
- ハイパーパラメータ調整
- 交差検証
- モデル評価

5. 結果解釈・可視化
- 特徴量重要度分析
- 予測結果の可視化
- ビジネスインサイトの抽出

6. デプロイメント・運用
- モデルの本番投入
- 性能監視
- 再訓練・更新

使用ツール：Python/R、Jupyter Notebook、pandas、scikit-learn、TensorFlow、Tableau、Power BIなど。

データサイエンスは技術だけでなく、ビジネス理解とコミュニケーション能力も重要です。""",
                "metadata": {"category": "data_science", "process": "workflow", "level": "advanced"}
            },
            {
                "filename": "mobile_app_development.txt",
                "content": """モバイルアプリ開発手法

モバイルアプリ開発には、ネイティブ開発とクロスプラットフォーム開発の選択肢があります。

ネイティブ開発：
iOS開発：
- Swift: モダンで高性能
- Objective-C: レガシーコード
- Xcode: 統合開発環境
- SwiftUI: 宣言的UI

Android開発：
- Kotlin: Google推奨言語
- Java: 従来からの標準
- Android Studio: 公式IDE
- Jetpack Compose: モダンUI

クロスプラットフォーム開発：
- React Native: Facebookが開発
- Flutter: Googleが開発、Dart言語
- Xamarin: Microsoft製、C#使用
- Ionic: ウェブ技術ベース

選択基準：
- 開発速度 vs パフォーマンス
- チームのスキルセット
- アプリの複雑さ
- 予算と期間

モバイル開発の考慮事項：
- ユーザビリティ・アクセシビリティ
- バッテリー消費
- ネットワーク効率
- セキュリティ
- ストア審査ガイドライン

最近のトレンド：
- Progressive Web Apps (PWA)
- AMP (Accelerated Mobile Pages)
- モバイルファーストデザイン
- マイクロインタラクション""",
                "metadata": {"category": "mobile_development", "platforms": ["ios", "android"], "level": "intermediate"}
            }
        ]
        
        # ファイル作成と処理
        for file_info in search_samples:
            file_path = project_root / file_info["filename"]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info["content"])
            
            document_id = await service.process_file_enhanced(
                str(file_path), 
                file_info["metadata"],
                extract_entities=True,
                analyze_sentiment=False
            )
            
            if document_id:
                logger.info(f"  ✅ Created: {file_info['filename']}")
            
            # クリーンアップ
            if file_path.exists():
                file_path.unlink()
        
        logger.info("📝 Search sample documents created\n")
        
    except Exception as e:
        logger.error(f"Failed to create search samples: {e}")

async def prompt_search_demo(service: EnhancedDocumentService):
    """プロンプト検索デモ"""
    try:
        logger.info("🔍 Prompt-Based Search Demo:")
        
        # 様々なプロンプトでテスト
        search_prompts = [
            {
                "prompt": "Pythonでデータ分析をしたい初心者向けの情報",
                "description": "Python + データ分析の組み合わせ検索"
            },
            {
                "prompt": "ウェブアプリケーションを作るためのフレームワーク",
                "description": "ウェブ開発フレームワーク検索"
            },
            {
                "prompt": "機械学習のアルゴリズムを選ぶ方法",
                "description": "機械学習アルゴリズム選択"
            },
            {
                "prompt": "スマートフォンアプリ開発の最新技術",
                "description": "モバイル開発技術"
            },
            {
                "prompt": "データを可視化する方法とツール",
                "description": "データ可視化手法"
            }
        ]
        
        for prompt_info in search_prompts:
            logger.info(f"\n  📝 Prompt: '{prompt_info['prompt']}'")
            logger.info(f"  🎯 Purpose: {prompt_info['description']}")
            
            # プロンプト検索実行
            results = await service.search_by_prompt(
                prompt_info["prompt"],
                similarity_threshold=0.6,
                max_results=3,
                include_scores=True
            )
            
            if results:
                logger.info(f"  📊 Found {len(results)} matching documents:")
                for i, result in enumerate(results, 1):
                    score = result.get('similarity_score', 0)
                    logger.info(f"    {i}. {result['title']} (Score: {score:.3f})")
                    logger.info(f"       Type: {result['file_type']}, Tags: {', '.join(result['tags'][:3])}")
                    logger.info(f"       Preview: {result['content_snippet'][:100]}...")
            else:
                logger.info("  ❌ No matching documents found")
        
        logger.info("\n🔍 Prompt search demo completed\n")
        
    except Exception as e:
        logger.error(f"Prompt search demo failed: {e}")

async def similar_documents_demo(service: EnhancedDocumentService):
    """類似ドキュメント検索デモ"""
    try:
        logger.info("🔗 Similar Documents Search Demo:")
        
        # テスト用の参照テキスト
        reference_texts = [
            {
                "text": "プログラミング言語の選び方と特徴を比較したい",
                "description": "プログラミング言語比較"
            },
            {
                "text": "機械学習プロジェクトを始めるために必要な手順",
                "description": "ML プロジェクト開始"
            },
            {
                "text": "ウェブサイトの性能を向上させる技術的手法",
                "description": "ウェブ性能最適化"
            }
        ]
        
        for ref_info in reference_texts:
            logger.info(f"\n  📄 Reference: '{ref_info['text']}'")
            logger.info(f"  🎯 Topic: {ref_info['description']}")
            
            # 類似ドキュメント検索
            similar_docs = await service.find_similar_documents_advanced(
                ref_info["text"],
                similarity_threshold=0.7,
                max_results=3
            )
            
            if similar_docs:
                logger.info(f"  🔗 Found {len(similar_docs)} similar documents:")
                for i, doc in enumerate(similar_docs, 1):
                    score = doc.get('similarity_score', 0)
                    logger.info(f"    {i}. {doc['title']} (Score: {score:.3f})")
                    
                    # 関係性分析結果表示
                    if doc.get('relationship_analysis'):
                        rel_analysis = doc['relationship_analysis']
                        logger.info(f"       Relationship: {rel_analysis.get('relation_type', 'unknown')} (Strength: {rel_analysis.get('strength', 0):.2f})")
                    
                    logger.info(f"       Preview: {doc['content_preview'][:80]}...")
            else:
                logger.info("  ❌ No similar documents found")
        
        logger.info("\n🔗 Similar documents demo completed\n")
        
    except Exception as e:
        logger.error(f"Similar documents demo failed: {e}")

async def diverse_prompt_test(service: EnhancedDocumentService):
    """多様なプロンプトテスト"""
    try:
        logger.info("🌈 Diverse Prompt Test:")
        
        # 様々なタイプのプロンプト
        diverse_prompts = [
            "初心者向けプログラミング学習",
            "データ可視化ツール",
            "モバイルアプリUI設計",
            "ニューラルネットワーク実装",
            "ウェブセキュリティ対策",
            "クラウドサービス比較",
            "アジャイル開発手法",
            "API設計ベストプラクティス"
        ]
        
        logger.info("  Testing various prompt types:")
        
        for prompt in diverse_prompts:
            logger.info(f"\n  🎯 Testing: '{prompt}'")
            
            # 知的検索とプロンプト検索を並行実行
            intelligent_results = await service.intelligent_search(
                prompt,
                search_type="hybrid",
                limit=2
            )
            
            prompt_results = await service.search_by_prompt(
                prompt,
                similarity_threshold=0.6,
                max_results=2
            )
            
            # 結果比較
            logger.info(f"    🧠 Intelligent search: {len(intelligent_results)} results")
            logger.info(f"    🔍 Prompt search: {len(prompt_results)} results")
            
            if intelligent_results:
                best_result = intelligent_results[0]
                logger.info(f"    📊 Best match: {best_result.document_title} (Score: {best_result.score:.3f})")
        
        logger.info("\n🌈 Diverse prompt test completed\n")
        
    except Exception as e:
        logger.error(f"Diverse prompt test failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Prompt search demo interrupted by user")
    except Exception as e:
        logger.error(f"Prompt search demo failed: {e}")
        sys.exit(1)