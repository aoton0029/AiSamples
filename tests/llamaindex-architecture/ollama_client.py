import asyncio
import logging
from typing import List, Optional, Dict, Any
import httpx
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain_community.embeddings import OllamaEmbeddings
from config import db_config

logger = logging.getLogger(__name__)

class EnhancedOllamaClient:
    """強化されたOllamaクライアント"""
    
    def __init__(self):
        self.base_url = db_config.OLLAMA_BASE_URL
        self.model = db_config.OLLAMA_MODEL
        self.embedding_model = db_config.OLLAMA_EMBEDDING_MODEL
        
        # LlamaIndex エンベディング
        self.embedding_client = None
        self.llm_client = None
        
        # LangChain エンベディング（代替）
        self.langchain_embedding = None
        
        # パフォーマンス統計
        self.stats = {
            "embeddings_generated": 0,
            "text_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # 簡易キャッシュ
        self.embedding_cache = {}
        self.max_cache_size = 1000
        
    async def initialize(self) -> bool:
        """クライアント初期化"""
        try:
            # LlamaIndex エンベディングクライアント初期化
            self.embedding_client = OllamaEmbedding(
                model_name=self.embedding_model,
                base_url=self.base_url,
                ollama_additional_kwargs={"mirostat": 0}
            )
            
            # LangChain エンベディング初期化（代替）
            self.langchain_embedding = LangchainEmbedding(
                OllamaEmbeddings(
                    base_url=self.base_url,
                    model=self.embedding_model
                )
            )
            
            # LLMクライアント初期化
            self.llm_client = Ollama(
                model=self.model,
                base_url=self.base_url,
                temperature=0.1,
                request_timeout=60.0
            )
            
            # モデルの可用性確認
            await self._check_model_availability()
            
            logger.info("Enhanced Ollama clients initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama clients: {e}")
            return False
    
    async def _check_model_availability(self):
        """モデルの可用性確認"""
        async with httpx.AsyncClient() as client:
            # 利用可能なモデル一覧取得
            response = await client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                
                # 必要なモデルが存在するか確認
                if self.model not in model_names:
                    logger.warning(f"LLM model {self.model} not found in Ollama")
                if self.embedding_model not in model_names:
                    logger.warning(f"Embedding model {self.embedding_model} not found in Ollama")
            else:
                logger.error(f"Failed to check Ollama models: {response.status_code}")
    
    
    async def generate_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """テキストのエンベディング生成（キャッシュ対応）"""
        try:
            # キャッシュ確認
            if use_cache:
                cache_key = hash(text)
                if cache_key in self.embedding_cache:
                    self.stats["cache_hits"] += 1
                    return self.embedding_cache[cache_key]
                else:
                    self.stats["cache_misses"] += 1
            
            if not self.embedding_client:
                await self.initialize()
            
            # エンベディング生成
            try:
                embedding = await self.embedding_client.aget_text_embedding(text)
            except Exception as e:
                # LlamaIndexが失敗した場合、LangChainを試行
                logger.warning(f"LlamaIndex embedding failed, trying LangChain: {e}")
                embedding = await self.langchain_embedding.aget_text_embedding(text)
            
            # キャッシュ保存
            if use_cache and embedding:
                if len(self.embedding_cache) >= self.max_cache_size:
                    # 古いエントリを削除
                    oldest_key = next(iter(self.embedding_cache))
                    del self.embedding_cache[oldest_key]
                
                cache_key = hash(text)
                self.embedding_cache[cache_key] = embedding
            
            self.stats["embeddings_generated"] += 1
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """バッチでエンベディング生成（最適化版）"""
        try:
            if not self.embedding_client:
                await self.initialize()
            
            embeddings = []
            
            # バッチ処理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = []
                
                # 並行処理でバッチ内のエンベディング生成
                tasks = [self.generate_embedding(text) for text in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch embedding error: {result}")
                        batch_embeddings.append(None)
                    else:
                        batch_embeddings.append(result)
                
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    async def generate_text(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> Optional[str]:
        """テキスト生成（パラメータ調整可能）"""
        try:
            if not self.llm_client:
                await self.initialize()
            
            # 一時的にtemperatureを設定
            original_temp = self.llm_client.temperature
            self.llm_client.temperature = temperature
            
            response = await self.llm_client.acomplete(
                prompt=prompt,
                max_tokens=max_tokens
            )
            
            # temperatureを元に戻す
            self.llm_client.temperature = original_temp
            
            self.stats["text_generated"] += 1
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            return None
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """感情分析"""
        prompt = f"""
以下のテキストの感情を分析してください：

テキスト: {text}

以下の形式で出力してください：
感情: [positive/negative/neutral]
強度: [0.0-1.0]
理由: [理由]
"""
        
        result = await self.generate_text(prompt, temperature=0.0)
        if result:
            try:
                lines = result.strip().split('\n')
                sentiment = lines[0].split(':')[1].strip()
                intensity = float(lines[1].split(':')[1].strip())
                reason = lines[2].split(':')[1].strip()
                
                return {
                    "sentiment": sentiment,
                    "intensity": intensity,
                    "reason": reason
                }
            except Exception as e:
                logger.error(f"Failed to parse sentiment analysis: {e}")
        
        return {"sentiment": "neutral", "intensity": 0.5, "reason": "Analysis failed"}
    
    async def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """エンティティ抽出"""
        prompt = f"""
以下のテキストから人名、組織名、場所名、日付などのエンティティを抽出してください：

テキスト: {text}

各エンティティを以下の形式で出力してください（1行に1つ）：
エンティティ名:タイプ:説明
"""
        
        result = await self.generate_text(prompt, temperature=0.0)
        entities = []
        
        if result:
            lines = result.strip().split('\n')
            for line in lines:
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        entities.append({
                            "name": parts[0].strip(),
                            "type": parts[1].strip(),
                            "description": parts[2].strip()
                        })
        
        return entities
    
    async def generate_summary_with_metadata(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """メタデータ付き要約生成"""
        summary = await self.summarize_text(text, max_length)
        
        # 追加メタデータ
        sentiment = await self.analyze_sentiment(text)
        entities = await self.extract_entities(text)
        keywords = await self.extract_keywords(text, max_keywords=5)
        
        return {
            "summary": summary,
            "sentiment": sentiment,
            "entities": entities,
            "keywords": keywords,
            "original_length": len(text),
            "summary_length": len(summary) if summary else 0
        }
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計取得"""
        return {
            **self.stats,
            "cache_size": len(self.embedding_cache),
            "cache_hit_ratio": self.stats["cache_hits"] / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
        }
    
    async def clear_cache(self):
        """キャッシュクリア"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    async def warm_up_models(self) -> bool:
        """モデルウォームアップ"""
        try:
            # テスト用のエンベディング生成
            test_embedding = await self.generate_embedding("test", use_cache=False)
            
            # テスト用のテキスト生成
            test_text = await self.generate_text("Hello", max_tokens=10)
            
            warm_up_success = test_embedding is not None and test_text is not None
            
            if warm_up_success:
                logger.info("Model warm-up completed successfully")
            else:
                logger.warning("Model warm-up partially failed")
            
            return warm_up_success
            
        except Exception as e:
            logger.error(f"Model warm-up failed: {e}")
            return False
    
    async def summarize_text(self, text: str, max_length: int = 200) -> Optional[str]:
        """テキスト要約"""
        prompt = f"""
以下のテキストを{max_length}文字以内で要約してください：

{text}

要約：
"""
        return await self.generate_text(prompt)
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """キーワード抽出"""
        prompt = f"""
以下のテキストから重要なキーワードを{max_keywords}個以内で抽出してください。
各キーワードは改行で区切って出力してください：

{text}

キーワード：
"""
        
        result = await self.generate_text(prompt)
        if result:
            keywords = [kw.strip() for kw in result.split('\n') if kw.strip()]
            return keywords[:max_keywords]
        return []
    
    async def analyze_document_relations(self, doc1_content: str, doc2_content: str) -> Optional[dict]:
        """ドキュメント間関係分析"""
        prompt = f"""
以下の2つのドキュメントの関係性を分析してください：

ドキュメント1：
{doc1_content[:500]}...

ドキュメント2：
{doc2_content[:500]}...

関係性の種類（similar, references, contains, related, unrelated）と
強度（0.0-1.0）、理由を以下の形式で出力してください：

関係性: [種類]
強度: [0.0-1.0]
理由: [理由]
"""
        
        result = await self.generate_text(prompt)
        if result:
            try:
                lines = result.strip().split('\n')
                relation_type = lines[0].split(':')[1].strip()
                strength = float(lines[1].split(':')[1].strip())
                reason = lines[2].split(':')[1].strip()
                
                return {
                    "relation_type": relation_type,
                    "strength": strength,
                    "reason": reason
                }
            except Exception as e:
                logger.error(f"Failed to parse relation analysis: {e}")
        
        return None
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

# グローバルインスタンス
ollama_client = EnhancedOllamaClient()