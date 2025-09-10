import asyncio
import logging
import time
from typing import List, Dict, Any
import json
from pathlib import Path

from enhanced_document_service import EnhancedDocumentService

logger = logging.getLogger(__name__)

class PromptSearchBenchmark:
    """プロンプト検索性能ベンチマーク"""
    
    def __init__(self, service: EnhancedDocumentService):
        self.service = service
        self.results = []
    
    async def run_benchmark(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ベンチマーク実行"""
        logger.info("🚀 Starting prompt search benchmark...")
        
        total_start_time = time.time()
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"📝 Test case {i+1}/{len(test_cases)}: {test_case['name']}")
            
            # 各検索手法をテスト
            case_results = await self._run_single_test_case(test_case)
            self.results.append(case_results)
        
        total_time = time.time() - total_start_time
        
        # 統計計算
        benchmark_stats = self._calculate_benchmark_stats(total_time)
        
        logger.info("🏁 Benchmark completed!")
        return benchmark_stats
    
    async def _run_single_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """単一テストケース実行"""
        prompt = test_case['prompt']
        expected_topics = test_case.get('expected_topics', [])
        
        case_result = {
            'name': test_case['name'],
            'prompt': prompt,
            'expected_topics': expected_topics,
            'methods': {}
        }
        
        # 1. プロンプト検索
        start_time = time.time()
        prompt_results = await self.service.search_by_prompt(
            prompt,
            similarity_threshold=0.6,
            max_results=5
        )
        prompt_time = time.time() - start_time
        
        case_result['methods']['prompt_search'] = {
            'execution_time': prompt_time,
            'result_count': len(prompt_results),
            'results': prompt_results[:3],  # 上位3件のみ保存
            'avg_score': sum([r.get('similarity_score', 0) for r in prompt_results]) / max(1, len(prompt_results))
        }
        
        # 2. 知的検索
        start_time = time.time()
        intelligent_results = await self.service.intelligent_search(
            prompt,
            search_type="hybrid",
            limit=5
        )
        intelligent_time = time.time() - start_time
        
        case_result['methods']['intelligent_search'] = {
            'execution_time': intelligent_time,
            'result_count': len(intelligent_results),
            'results': [{'title': r.document_title, 'score': r.score} for r in intelligent_results[:3]],
            'avg_score': sum([r.score for r in intelligent_results]) / max(1, len(intelligent_results))
        }
        
        # 3. ベクトル検索のみ
        start_time = time.time()
        vector_results = await self.service.intelligent_search(
            prompt,
            search_type="vector",
            limit=5
        )
        vector_time = time.time() - start_time
        
        case_result['methods']['vector_search'] = {
            'execution_time': vector_time,
            'result_count': len(vector_results),
            'results': [{'title': r.document_title, 'score': r.score} for r in vector_results[:3]],
            'avg_score': sum([r.score for r in vector_results]) / max(1, len(vector_results))
        }
        
        # 関連性評価
        case_result['relevance_evaluation'] = self._evaluate_relevance(
            prompt_results, expected_topics
        )
        
        return case_result
    
    def _evaluate_relevance(self, results: List[Dict], expected_topics: List[str]) -> Dict[str, Any]:
        """関連性評価"""
        if not expected_topics:
            return {'score': 0.0, 'explanation': 'No expected topics provided'}
        
        relevant_count = 0
        total_results = len(results)
        
        for result in results:
            tags = result.get('tags', [])
            title = result.get('title', '').lower()
            
            # タグや タイトルに期待トピックが含まれているかチェック
            for topic in expected_topics:
                if (topic.lower() in title or 
                    any(topic.lower() in tag.lower() for tag in tags)):
                    relevant_count += 1
                    break
        
        relevance_score = relevant_count / max(1, total_results)
        
        return {
            'score': relevance_score,
            'relevant_count': relevant_count,
            'total_count': total_results,
            'explanation': f'{relevant_count}/{total_results} results matched expected topics'
        }
    
    def _calculate_benchmark_stats(self, total_time: float) -> Dict[str, Any]:
        """ベンチマーク統計計算"""
        stats = {
            'total_execution_time': total_time,
            'total_test_cases': len(self.results),
            'method_performance': {},
            'overall_metrics': {}
        }
        
        # 各手法の統計
        methods = ['prompt_search', 'intelligent_search', 'vector_search']
        
        for method in methods:
            method_times = []
            method_scores = []
            method_counts = []
            
            for result in self.results:
                if method in result['methods']:
                    method_data = result['methods'][method]
                    method_times.append(method_data['execution_time'])
                    method_scores.append(method_data['avg_score'])
                    method_counts.append(method_data['result_count'])
            
            if method_times:
                stats['method_performance'][method] = {
                    'avg_execution_time': sum(method_times) / len(method_times),
                    'min_execution_time': min(method_times),
                    'max_execution_time': max(method_times),
                    'avg_score': sum(method_scores) / len(method_scores),
                    'avg_result_count': sum(method_counts) / len(method_counts)
                }
        
        # 関連性統計
        relevance_scores = [r['relevance_evaluation']['score'] for r in self.results]
        if relevance_scores:
            stats['overall_metrics']['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)
            stats['overall_metrics']['min_relevance'] = min(relevance_scores)
            stats['overall_metrics']['max_relevance'] = max(relevance_scores)
        
        return stats
    
    def save_results(self, filename: str):
        """結果保存"""
        output_data = {
            'benchmark_results': self.results,
            'timestamp': time.time(),
            'test_count': len(self.results)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📊 Benchmark results saved to {filename}")

async def main():
    """ベンチマークテスト実行"""
    
    # テストケース定義
    test_cases = [
        {
            'name': 'Python Programming Query',
            'prompt': 'Pythonでデータ分析を始めたい初心者向けの情報',
            'expected_topics': ['python', 'programming', 'data']
        },
        {
            'name': 'Machine Learning Algorithm Selection',
            'prompt': '分類問題に最適な機械学習アルゴリズムを選びたい',
            'expected_topics': ['machine_learning', 'algorithms', 'classification']
        },
        {
            'name': 'Web Development Framework',
            'prompt': 'モダンなウェブアプリケーション開発フレームワーク',
            'expected_topics': ['web', 'development', 'framework']
        },
        {
            'name': 'Mobile App Development',
            'prompt': 'クロスプラットフォームモバイルアプリ開発手法',
            'expected_topics': ['mobile', 'development', 'cross_platform']
        },
        {
            'name': 'Data Visualization Tools',
            'prompt': 'データの可視化に使えるツールとライブラリ',
            'expected_topics': ['data', 'visualization', 'tools']
        },
        {
            'name': 'AI Research Trends',
            'prompt': '人工知能研究の最新動向と技術',
            'expected_topics': ['ai', 'research', 'technology']
        },
        {
            'name': 'Database Technology',
            'prompt': 'スケーラブルなデータベース設計手法',
            'expected_topics': ['database', 'scalability', 'design']
        },
        {
            'name': 'Cloud Computing Services',
            'prompt': 'クラウドサービスの選択と比較',
            'expected_topics': ['cloud', 'services', 'comparison']
        }
    ]
    
    service = None
    
    try:
        logger.info("=== Prompt Search Benchmark ===")
        
        # サービス初期化
        service = EnhancedDocumentService()
        success = await service.initialize()
        
        if not success:
            logger.error("Failed to initialize service")
            return
        
        # ベンチマーク実行
        benchmark = PromptSearchBenchmark(service)
        stats = await benchmark.run_benchmark(test_cases)
        
        # 結果表示
        logger.info("\n📊 Benchmark Results Summary:")
        logger.info(f"Total execution time: {stats['total_execution_time']:.2f} seconds")
        logger.info(f"Total test cases: {stats['total_test_cases']}")
        
        if 'method_performance' in stats:
            logger.info("\n⚡ Performance by Method:")
            for method, perf in stats['method_performance'].items():
                logger.info(f"  {method}:")
                logger.info(f"    Average time: {perf['avg_execution_time']:.3f}s")
                logger.info(f"    Average score: {perf['avg_score']:.3f}")
                logger.info(f"    Average results: {perf['avg_result_count']:.1f}")
        
        if 'overall_metrics' in stats:
            logger.info(f"\n🎯 Overall Relevance: {stats['overall_metrics'].get('avg_relevance', 0):.2%}")
        
        # 結果保存
        benchmark.save_results('prompt_search_benchmark_results.json')
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
    
    finally:
        if service:
            await service.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())