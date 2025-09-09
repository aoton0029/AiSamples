"""
高速インデックス作成と検索のためのユーティリティクラス
"""

from typing import List, Dict, Any, Optional, Union
import asyncio
import concurrent.futures
from pathlib import Path
import time

from llama_index.core import Document
from llama_index.core.schema import BaseNode

from .llamaindex_db_manager import LlamaIndexDBManager


class FastIndexBuilder:
    """高速インデックス構築用ユーティリティ"""
    
    def __init__(self, manager: LlamaIndexDBManager):
        self.manager = manager
        
    def batch_create_indexes(self, data_sources: List[Dict[str, Any]], 
                           max_workers: int = 4) -> Dict[str, bool]:
        """複数のデータソースから並列でインデックス作成"""
        
        results = {}
        
        def create_single_index(source_config):
            try:
                index_name = source_config["index_name"]
                source_type = source_config["type"]
                
                if source_type == "directory":
                    self.manager.create_index_from_directory(
                        source_config["path"], index_name
                    )
                elif source_type == "files":
                    self.manager.create_index_from_files(
                        source_config["files"], index_name
                    )
                elif source_type == "documents":
                    self.manager.create_index_from_documents(
                        source_config["documents"], index_name
                    )
                
                return index_name, True
                
            except Exception as e:
                print(f"インデックス作成エラー {source_config['index_name']}: {e}")
                return source_config["index_name"], False
        
        # 並列実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_source = {
                executor.submit(create_single_index, source): source 
                for source in data_sources
            }
            
            for future in concurrent.futures.as_completed(future_to_source):
                index_name, success = future.result()
                results[index_name] = success
        
        return results
    
    def incremental_update(self, index_name: str, new_documents: List[Document],
                          batch_size: int = 50) -> bool:
        """インクリメンタルな更新（バッチ処理）"""
        
        try:
            total_docs = len(new_documents)
            processed = 0
            
            # バッチごとに処理
            for i in range(0, total_docs, batch_size):
                batch = new_documents[i:i + batch_size]
                
                success = self.manager.add_documents_to_index(batch, index_name)
                if not success:
                    print(f"バッチ {i//batch_size + 1} の処理に失敗")
                    return False
                
                processed += len(batch)
                print(f"進捗: {processed}/{total_docs} ドキュメント処理完了")
            
            return True
            
        except Exception as e:
            print(f"インクリメンタル更新エラー: {e}")
            return False


class SmartRetriever:
    """スマート検索とキャッシュ機能"""
    
    def __init__(self, manager: LlamaIndexDBManager):
        self.manager = manager
        self.query_cache = {}
        self.cache_timeout = 300  # 5分
        
    def smart_search(self, query: str, indexes: List[str], 
                    top_k: int = 5, use_cache: bool = True) -> List[Dict[str, Any]]:
        """複数インデックスからのスマート検索"""
        
        # キャッシュチェック
        cache_key = f"{query}_{'-'.join(indexes)}_{top_k}"
        
        if use_cache and cache_key in self.query_cache:
            cached_result, timestamp = self.query_cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                print("キャッシュから結果を返却")
                return cached_result
        
        # 各インデックスから検索
        all_results = []
        
        for index_name in indexes:
            try:
                results = self.manager.search(query, top_k, index_name)
                
                # インデックス名を結果に追加
                for result in results:
                    result["source_index"] = index_name
                
                all_results.extend(results)
                
            except Exception as e:
                print(f"インデックス {index_name} での検索エラー: {e}")
                continue
        
        # スコアでソート
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # 上位結果を選択
        final_results = all_results[:top_k]
        
        # キャッシュに保存
        if use_cache:
            self.query_cache[cache_key] = (final_results, time.time())
        
        return final_results
    
    def semantic_search_with_filter(self, query: str, index_name: str,
                                   metadata_filters: Dict[str, Any] = None,
                                   score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """セマンティック検索とフィルタリング"""
        
        # 基本検索
        results = self.manager.search(query, top_k=20, index_name=index_name)
        
        # スコアフィルタリング
        filtered_results = [
            result for result in results 
            if result.get("score", 0) >= score_threshold
        ]
        
        # メタデータフィルタリング
        if metadata_filters:
            final_results = []
            for result in filtered_results:
                metadata = result.get("metadata", {})
                match = True
                
                for key, value in metadata_filters.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                
                if match:
                    final_results.append(result)
            
            return final_results
        
        return filtered_results
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.query_cache.clear()
        print("検索キャッシュをクリアしました")


class RAGOptimizer:
    """RAG最適化ユーティリティ"""
    
    def __init__(self, manager: LlamaIndexDBManager):
        self.manager = manager
        
    def optimize_chunk_size(self, documents: List[Document], 
                           test_queries: List[str],
                           chunk_sizes: List[int] = [512, 1024, 2048]) -> Dict[str, Any]:
        """最適なチャンクサイズを見つける"""
        
        results = {}
        
        for chunk_size in chunk_sizes:
            print(f"チャンクサイズ {chunk_size} をテスト中...")
            
            # 一時的にチャンクサイズを変更
            original_chunk_size = self.manager.config.get("chunk_size", 1024)
            self.manager.config["chunk_size"] = chunk_size
            
            # テストインデックス作成
            test_index_name = f"test_chunk_{chunk_size}"
            
            try:
                start_time = time.time()
                self.manager.create_index_from_documents(documents, test_index_name)
                creation_time = time.time() - start_time
                
                # テストクエリで評価
                total_relevance = 0
                query_times = []
                
                for query in test_queries:
                    query_start = time.time()
                    search_results = self.manager.search(query, top_k=5, index_name=test_index_name)
                    query_time = time.time() - query_start
                    
                    query_times.append(query_time)
                    
                    # 簡単な関連性スコア（実際の評価では他の指標も使用）
                    if search_results:
                        avg_score = sum(r.get("score", 0) for r in search_results) / len(search_results)
                        total_relevance += avg_score
                
                avg_relevance = total_relevance / len(test_queries) if test_queries else 0
                avg_query_time = sum(query_times) / len(query_times) if query_times else 0
                
                results[chunk_size] = {
                    "creation_time": creation_time,
                    "avg_query_time": avg_query_time,
                    "avg_relevance": avg_relevance,
                    "total_score": avg_relevance / avg_query_time if avg_query_time > 0 else 0
                }
                
                # テストインデックス削除
                self.manager.delete_index(test_index_name)
                
            except Exception as e:
                print(f"チャンクサイズ {chunk_size} でエラー: {e}")
                results[chunk_size] = {"error": str(e)}
            
            # 元の設定に戻す
            self.manager.config["chunk_size"] = original_chunk_size
        
        # 最適なチャンクサイズを推奨
        best_chunk_size = max(
            [size for size, result in results.items() if "error" not in result],
            key=lambda size: results[size].get("total_score", 0),
            default=1024
        )
        
        results["recommended"] = best_chunk_size
        
        return results
    
    def benchmark_search_performance(self, index_name: str, 
                                   test_queries: List[str],
                                   top_k_values: List[int] = [1, 5, 10, 20]) -> Dict[str, Any]:
        """検索パフォーマンスのベンチマーク"""
        
        benchmark_results = {}
        
        for top_k in top_k_values:
            print(f"top_k={top_k} でベンチマーク実行中...")
            
            times = []
            result_counts = []
            
            for query in test_queries:
                start_time = time.time()
                results = self.manager.search(query, top_k=top_k, index_name=index_name)
                search_time = time.time() - start_time
                
                times.append(search_time)
                result_counts.append(len(results))
            
            benchmark_results[top_k] = {
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "avg_results": sum(result_counts) / len(result_counts),
                "total_queries": len(test_queries)
            }
        
        return benchmark_results