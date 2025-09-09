import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
from datetime import datetime
import re

from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import VectorStoreQuery
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.graph_stores.neo4j import Neo4jGraphStore

from ollama_connector import OllamaConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """検索フィルタ条件"""
    keywords: List[str] = None
    tags: List[str] = None
    authors: List[str] = None
    date_range: Tuple[datetime, datetime] = None
    source: str = None
    min_score: float = 0.0


@dataclass
class SearchResult:
    """検索結果"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source_db: str
    highlights: List[str] = None
    related_entities: List[str] = None


class DocumentRetriever:
    """マルチDB対応のドキュメント検索・RAGクラス"""
    
    def __init__(
        self,
        ollama_connector: OllamaConnector,
        vector_store: MilvusVectorStore,
        doc_store: MongoDocumentStore,
        graph_store: Neo4jGraphStore,
        vector_top_k: int = 20,
        final_top_k: int = 10
    ):
        self.ollama = ollama_connector
        self.vector_store = vector_store
        self.doc_store = doc_store
        self.graph_store = graph_store
        self.vector_top_k = vector_top_k
        self.final_top_k = final_top_k
        
        # インデックスとクエリエンジンの初期化
        self._initialize_components()
    
    def _initialize_components(self):
        """コンポーネントの初期化"""
        # ベクトルインデックスの作成
        self.vector_index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.ollama.embedding_model
        )
        
        # レトリーバーの初期化
        self.vector_retriever = VectorIndexRetriever(
            index=self.vector_index,
            similarity_top_k=self.vector_top_k
        )
        
        # 応答合成器の初期化
        self.response_synthesizer = get_response_synthesizer(
            llm=self.ollama.llm,
            response_mode="tree_summarize"
        )
        
        # クエリエンジンの初期化
        self.query_engine = RetrieverQueryEngine(
            retriever=self.vector_retriever,
            response_synthesizer=self.response_synthesizer
        )
    
    def preprocess_query(self, query: str, filters: Optional[SearchFilter] = None) -> QueryBundle:
        """1. クエリ入力と前処理"""
        logger.info(f"クエリ前処理開始: {query}")
        
        # クエリの正規化
        normalized_query = self._normalize_query(query)
        
        # 意図解析（簡単な実装）
        intent = self._analyze_intent(normalized_query)
        
        # クエリバンドルの作成
        query_bundle = QueryBundle(
            query_str=normalized_query,
            custom_embedding_strs=[normalized_query],
            embedding=None  # 後で生成
        )
        
        # フィルタ条件の処理
        if filters:
            query_bundle.metadata = self._process_filters(filters)
        
        logger.info(f"前処理完了 - 意図: {intent}")
        return query_bundle
    
    def _normalize_query(self, query: str) -> str:
        """クエリの正規化"""
        # 基本的な正規化
        query = query.strip().lower()
        # 特殊文字の処理
        query = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', query)
        # 複数スペースを単一スペースに
        query = re.sub(r'\s+', ' ', query)
        return query
    
    def _analyze_intent(self, query: str) -> str:
        """簡単な意図解析"""
        # キーワードベースの意図分類
        if any(word in query for word in ['what', 'what is', 'define', '何', 'とは']):
            return 'definition'
        elif any(word in query for word in ['how', 'howto', 'tutorial', 'どうやって', '方法']):
            return 'howto'
        elif any(word in query for word in ['why', 'reason', 'なぜ', '理由']):
            return 'explanation'
        else:
            return 'general'
    
    def _process_filters(self, filters: SearchFilter) -> Dict[str, Any]:
        """フィルタ条件の処理"""
        metadata = {}
        
        if filters.keywords:
            metadata['keywords'] = filters.keywords
        if filters.tags:
            metadata['tags'] = filters.tags
        if filters.authors:
            metadata['authors'] = filters.authors
        if filters.date_range:
            metadata['date_range'] = filters.date_range
        if filters.source:
            metadata['source'] = filters.source
        if filters.min_score:
            metadata['min_score'] = filters.min_score
        
        return metadata
    
    def vector_search(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """2. ベクトル検索（Semantic retrieval）"""
        logger.info("ベクトル検索開始")
        
        try:
            # クエリの埋め込み生成
            if not query_bundle.embedding:
                query_embedding = self.ollama.embedding_model.get_text_embedding(
                    query_bundle.query_str
                )
                query_bundle.embedding = query_embedding
            
            # ベクトル検索の実行
            vector_results = self.vector_retriever.retrieve(query_bundle)
            
            logger.info(f"ベクトル検索完了: {len(vector_results)}件取得")
            return vector_results
            
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {e}")
            return []
    
    def keyword_filter_search(
        self, 
        query_bundle: QueryBundle, 
        vector_results: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """3. キーワード／フィルタ検索（Precision）"""
        logger.info("キーワード・フィルタ検索開始")
        
        filtered_results = []
        
        try:
            # ベクトル検索結果のフィルタリング
            for node_with_score in vector_results:
                if self._apply_filters(node_with_score, query_bundle):
                    filtered_results.append(node_with_score)
            
            # MongoDBでの追加キーワード検索
            mongo_results = self._mongodb_keyword_search(query_bundle)
            
            # 結果のマージ（重複除去）
            merged_results = self._merge_results(filtered_results, mongo_results)
            
            logger.info(f"フィルタ検索完了: {len(merged_results)}件")
            return merged_results
            
        except Exception as e:
            logger.error(f"フィルタ検索エラー: {e}")
            return vector_results  # フィルタ失敗時は元の結果を返す
    
    def _apply_filters(self, node_with_score: NodeWithScore, query_bundle: QueryBundle) -> bool:
        """ノードにフィルタを適用"""
        if not hasattr(query_bundle, 'metadata') or not query_bundle.metadata:
            return True
        
        node = node_with_score.node
        metadata = node.metadata
        filters = query_bundle.metadata
        
        # キーワードフィルタ
        if 'keywords' in filters:
            keywords = filters['keywords']
            content = node.get_content().lower()
            if not any(keyword.lower() in content for keyword in keywords):
                return False
        
        # タグフィルタ
        if 'tags' in filters:
            node_tags = metadata.get('tags', [])
            required_tags = filters['tags']
            if not any(tag in node_tags for tag in required_tags):
                return False
        
        # 作者フィルタ
        if 'authors' in filters:
            node_author = metadata.get('author', '').lower()
            required_authors = [a.lower() for a in filters['authors']]
            if node_author not in required_authors:
                return False
        
        # スコアフィルタ
        if 'min_score' in filters:
            if node_with_score.score < filters['min_score']:
                return False
        
        return True
    
    def _mongodb_keyword_search(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """MongoDBでのキーワード検索"""
        try:
            # ここでMongoDBの全文検索を実装
            # 簡単な実装例
            search_results = []
            # 実際のMongoDB検索ロジックをここに実装
            return search_results
        except Exception as e:
            logger.error(f"MongoDB検索エラー: {e}")
            return []
    
    def _merge_results(
        self, 
        vector_results: List[NodeWithScore], 
        mongo_results: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """結果のマージ（重複除去）"""
        seen_ids = set()
        merged = []
        
        # ベクトル検索結果を優先
        for result in vector_results:
            node_id = result.node.node_id
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                merged.append(result)
        
        # MongoDB結果を追加
        for result in mongo_results:
            node_id = result.node.node_id
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                merged.append(result)
        
        return merged
    
    def graph_expansion(self, search_results: List[NodeWithScore]) -> List[NodeWithScore]:
        """4. グラフ拡張（関係性補強）"""
        logger.info("グラフ拡張開始")
        
        expanded_results = list(search_results)  # コピーを作成
        
        try:
            for node_with_score in search_results:
                doc_id = node_with_score.node.metadata.get('doc_id')
                if not doc_id:
                    continue
                
                # 関連エンティティの取得
                related_entities = self._get_related_entities(doc_id)
                
                # 関連ドキュメントの取得
                related_docs = self._get_related_documents(doc_id, related_entities)
                
                # 関係性スコアの計算とブースト
                boosted_score = self._calculate_graph_boost(
                    node_with_score.score, 
                    related_entities, 
                    related_docs
                )
                
                # スコアの更新
                node_with_score.score = boosted_score
                
                # 関連情報をメタデータに追加
                node_with_score.node.metadata['related_entities'] = related_entities
                node_with_score.node.metadata['related_documents'] = related_docs
            
            logger.info(f"グラフ拡張完了: {len(expanded_results)}件")
            return expanded_results
            
        except Exception as e:
            logger.error(f"グラフ拡張エラー: {e}")
            return search_results
    
    def _get_related_entities(self, doc_id: str) -> List[str]:
        """関連エンティティの取得"""
        try:
            # Neo4jクエリでエンティティを取得
            query = """
            MATCH (d:Document {doc_id: $doc_id})-[:CONTAINS_ENTITY]->(e:Entity)
            RETURN e.name as entity_name
            """
            
            # 実際のNeo4jクエリ実行は簡略化
            # result = self.graph_store.query(query, {"doc_id": doc_id})
            # return [record["entity_name"] for record in result]
            
            return []  # 簡単な実装
        except Exception as e:
            logger.error(f"エンティティ取得エラー: {e}")
            return []
    
    def _get_related_documents(self, doc_id: str, entities: List[str]) -> List[str]:
        """関連ドキュメントの取得"""
        try:
            if not entities:
                return []
            
            # 同じエンティティを含む他のドキュメントを取得
            query = """
            MATCH (e:Entity)<-[:CONTAINS_ENTITY]-(d1:Document {doc_id: $doc_id})
            MATCH (e)<-[:CONTAINS_ENTITY]-(d2:Document)
            WHERE d1 <> d2
            RETURN DISTINCT d2.doc_id as related_doc_id
            LIMIT 5
            """
            
            # 実際のクエリ実行は簡略化
            return []
        except Exception as e:
            logger.error(f"関連ドキュメント取得エラー: {e}")
            return []
    
    def _calculate_graph_boost(
        self, 
        original_score: float, 
        entities: List[str], 
        related_docs: List[str]
    ) -> float:
        """グラフ関係性によるスコアブースト計算"""
        boost_factor = 1.0
        
        # エンティティ数による軽微なブースト
        if entities:
            boost_factor += len(entities) * 0.01
        
        # 関連ドキュメント数によるブースト
        if related_docs:
            boost_factor += len(related_docs) * 0.05
        
        return original_score * boost_factor
    
    def rerank_results(self, search_results: List[NodeWithScore]) -> List[NodeWithScore]:
        """5. 再ランキング（Rerank）"""
        logger.info("再ランキング開始")
        
        try:
            # 複数スコアによる再ランキング
            for node_with_score in search_results:
                # 総合スコアの計算
                final_score = self._calculate_final_score(node_with_score)
                node_with_score.score = final_score
            
            # スコア順でソート
            ranked_results = sorted(
                search_results, 
                key=lambda x: x.score, 
                reverse=True
            )[:self.final_top_k]
            
            logger.info(f"再ランキング完了: {len(ranked_results)}件")
            return ranked_results
            
        except Exception as e:
            logger.error(f"再ランキングエラー: {e}")
            return search_results[:self.final_top_k]
    
    def _calculate_final_score(self, node_with_score: NodeWithScore) -> float:
        """最終スコアの計算"""
        base_score = node_with_score.score
        metadata = node_with_score.node.metadata
        
        # メタデータブースト
        metadata_boost = 1.0
        
        # 新しさによるブースト
        if 'indexed_at' in metadata:
            try:
                indexed_date = datetime.fromisoformat(metadata['indexed_at'])
                days_old = (datetime.utcnow() - indexed_date).days
                if days_old < 30:  # 30日以内は軽微なブースト
                    metadata_boost += 0.1
            except:
                pass
        
        # タグ一致によるブースト
        if 'tags' in metadata:
            tags = metadata['tags']
            if tags and len(tags) > 0:
                metadata_boost += len(tags) * 0.02
        
        return base_score * metadata_boost
    
    def format_results(self, search_results: List[NodeWithScore]) -> List[SearchResult]:
        """6. 結果合成と返却"""
        logger.info("結果フォーマット開始")
        
        formatted_results = []
        
        for node_with_score in search_results:
            node = node_with_score.node
            
            # ハイライト生成
            highlights = self._generate_highlights(node)
            
            # 検索結果オブジェクトの作成
            result = SearchResult(
                doc_id=node.metadata.get('doc_id', node.node_id),
                content=node.get_content()[:500] + "..." if len(node.get_content()) > 500 else node.get_content(),
                metadata=node.metadata,
                score=node_with_score.score,
                source_db="vector_db",  # 実際はDBソースを判定
                highlights=highlights,
                related_entities=node.metadata.get('related_entities', [])
            )
            
            formatted_results.append(result)
        
        logger.info(f"結果フォーマット完了: {len(formatted_results)}件")
        return formatted_results
    
    def _generate_highlights(self, node) -> List[str]:
        """ハイライト生成"""
        content = node.get_content()
        # 簡単なハイライト生成（実際はより高度な実装が必要）
        sentences = content.split('。')[:3]  # 最初の3文
        return [s.strip() + '。' for s in sentences if s.strip()]
    
    def search(
        self, 
        query: str, 
        filters: Optional[SearchFilter] = None
    ) -> List[SearchResult]:
        """統合検索メソッド"""
        logger.info(f"検索開始: {query}")
        
        try:
            # 1. クエリ前処理
            query_bundle = self.preprocess_query(query, filters)
            
            # 2. ベクトル検索
            vector_results = self.vector_search(query_bundle)
            if not vector_results:
                logger.warning("ベクトル検索で結果が見つかりませんでした")
                return []
            
            # 3. キーワード・フィルタ検索
            filtered_results = self.keyword_filter_search(query_bundle, vector_results)
            
            # 4. グラフ拡張
            expanded_results = self.graph_expansion(filtered_results)
            
            # 5. 再ランキング
            ranked_results = self.rerank_results(expanded_results)
            
            # 6. 結果フォーマット
            final_results = self.format_results(ranked_results)
            
            logger.info(f"検索完了: {len(final_results)}件の結果")
            return final_results
            
        except Exception as e:
            logger.error(f"検索エラー: {e}")
            return []
    
    def rag_query(self, query: str, filters: Optional[SearchFilter] = None) -> str:
        """RAGクエリ（質問応答）"""
        logger.info(f"RAGクエリ開始: {query}")
        
        try:
            # 検索実行
            search_results = self.search(query, filters)
            
            if not search_results:
                return "申し訳ございませんが、関連する情報が見つかりませんでした。"
            
            # コンテキストの構築
            context = self._build_context(search_results)
            
            # RAGプロンプトの作成
            rag_prompt = self._create_rag_prompt(query, context)
            
            # LLMによる回答生成
            response = self.ollama.llm.complete(rag_prompt)
            
            logger.info("RAGクエリ完了")
            return response.text
            
        except Exception as e:
            logger.error(f"RAGクエリエラー: {e}")
            return f"エラーが発生しました: {str(e)}"
    
    def _build_context(self, search_results: List[SearchResult]) -> str:
        """検索結果からコンテキストを構築"""
        context_parts = []
        
        for i, result in enumerate(search_results[:5]):  # 上位5件を使用
            context_part = f"""
ドキュメント {i+1}:
タイトル: {result.metadata.get('title', 'Unknown')}
内容: {result.content}
スコア: {result.score:.3f}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str) -> str:
        """RAGプロンプトの作成"""
        prompt = f"""以下のコンテキスト情報を使用して、質問に回答してください。

コンテキスト:
{context}

質問: {query}

回答: コンテキストの情報に基づいて、正確で役立つ回答を提供してください。情報が不足している場合は、その旨を明記してください。
"""
        return prompt
    
    def record_feedback(
        self, 
        query: str, 
        doc_id: str, 
        feedback: str, 
        rating: float
    ):
        """7. フィードバック取り込み"""
        logger.info(f"フィードバック記録: {query} -> {doc_id} ({rating})")
        
        try:
            # フィードバックデータの保存（実装例）
            feedback_data = {
                "query": query,
                "doc_id": doc_id,
                "feedback": feedback,
                "rating": rating,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # MongoDBにフィードバックを保存
            # 実際の実装では専用のフィードバックコレクションに保存
            logger.info("フィードバック記録完了")
            
        except Exception as e:
            logger.error(f"フィードバック記録エラー: {e}")



def demo():
    from typing import List
    from datetime import datetime, timedelta

    from core.ollama_connector import OllamaConnector
    from document_indexer import DocumentIndexer
    from document_retriever import DocumentRetriever, SearchFilter
    from config import (
        DEFAULT_MILVUS_CONFIG,
        DEFAULT_MONGO_CONFIG,
        DEFAULT_NEO4J_CONFIG,
        DEFAULT_INDEXER_CONFIG,
        DEFAULT_RETRIEVER_CONFIG
    )


    def demo_retrieval():
        """検索・RAGのデモンストレーション"""
        
        # Ollamaコネクターの初期化
        ollama = OllamaConnector()
        ollama.initialize_llm(DEFAULT_INDEXER_CONFIG["llm_model"])
        ollama.initialize_embedding(DEFAULT_INDEXER_CONFIG["embedding_model"])
        
        # インデクサーの初期化（事前にドキュメントがインデックス化されている前提）
        indexer = DocumentIndexer(
            ollama_connector=ollama,
            milvus_config=DEFAULT_MILVUS_CONFIG,
            mongo_config=DEFAULT_MONGO_CONFIG,
            neo4j_config=DEFAULT_NEO4J_CONFIG
        )
        
        # レトリーバーの初期化
        retriever = DocumentRetriever(
            ollama_connector=ollama,
            vector_store=indexer.vector_store,
            doc_store=indexer.doc_store,
            graph_store=indexer.graph_store,
            vector_top_k=DEFAULT_RETRIEVER_CONFIG["vector_top_k"],
            final_top_k=DEFAULT_RETRIEVER_CONFIG["final_top_k"]
        )
        
        # 検索デモ
        print("=== 基本検索デモ ===")
        basic_query = "人工知能とは何ですか？"
        results = retriever.search(basic_query)
        
        print(f"クエリ: {basic_query}")
        print(f"検索結果: {len(results)}件")
        for i, result in enumerate(results):
            print(f"\n結果 {i+1}:")
            print(f"  ドキュメントID: {result.doc_id}")
            print(f"  タイトル: {result.metadata.get('title', 'Unknown')}")
            print(f"  スコア: {result.score:.3f}")
            print(f"  内容抜粋: {result.content[:100]}...")
            if result.related_entities:
                print(f"  関連エンティティ: {result.related_entities}")
        
        # フィルタ付き検索デモ
        print("\n=== フィルタ付き検索デモ ===")
        filter_query = "データサイエンス"
        search_filter = SearchFilter(
            tags=["データサイエンス", "統計学"],
            authors=["山田花子"],
            min_score=0.5
        )
        
        filtered_results = retriever.search(filter_query, search_filter)
        print(f"フィルタ付きクエリ: {filter_query}")
        print(f"フィルタ条件: tags={search_filter.tags}, authors={search_filter.authors}")
        print(f"検索結果: {len(filtered_results)}件")
        
        # RAGデモ
        print("\n=== RAG質問応答デモ ===")
        rag_questions = [
            "機械学習の主な手法について教えてください",
            "データサイエンスで重要な統計手法は何ですか？",
            "AIの応用分野にはどのようなものがありますか？"
        ]
        
        for question in rag_questions:
            print(f"\n質問: {question}")
            answer = retriever.rag_query(question)
            print(f"回答: {answer}")
            print("-" * 50)
        
        # フィードバックデモ
        print("\n=== フィードバックデモ ===")
        if results:
            retriever.record_feedback(
                query=basic_query,
                doc_id=results[0].doc_id,
                feedback="helpful",
                rating=4.5
            )
            print("フィードバックを記録しました")


    def demo_advanced_search():
        """高度な検索機能のデモ"""
        
        # 日付範囲フィルタのデモ
        print("=== 日付範囲フィルタデモ ===")
        
        # 過去30日間のドキュメントのみ検索
        recent_filter = SearchFilter(
            date_range=(
                datetime.utcnow() - timedelta(days=30),
                datetime.utcnow()
            )
        )
        
        # 複合検索のデモ
        print("=== 複合検索デモ ===")
        complex_filter = SearchFilter(
            keywords=["機械学習", "AI"],
            tags=["技術", "AI"],
            min_score=0.7
        )
        
        print("複合フィルタ条件:")
        print(f"  キーワード: {complex_filter.keywords}")
        print(f"  タグ: {complex_filter.tags}")
        print(f"  最小スコア: {complex_filter.min_score}")


    if __name__ == "__main__":
        print("ドキュメント検索・RAGシステムのデモを開始します")
        
        try:
            demo_retrieval()
            demo_advanced_search()
            print("\nデモ完了")
        except Exception as e:
            print(f"デモ実行エラー: {e}")