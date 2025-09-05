import asyncio
import grpc
from concurrent import futures
import sys
import os
from typing import List, Dict, Any

# Add proto path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from proto import mcp_service_pb2, mcp_service_pb2_grpc

from fastmcp import FastMCP
from transformers import AutoTokenizer
import nltk
import spacy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

class TokenizationServiceImpl(mcp_service_pb2_grpc.TokenizationServiceServicer):
    def __init__(self):
        self.mcp_app = FastMCP("TokenizationService")
        self.setup_tokenizers()
    
    def setup_tokenizers(self):
        """Initialize various tokenizers"""
        self.tokenizers = {}
        
        # Load default tokenizers
        try:
            self.tokenizers['bert'] = AutoTokenizer.from_pretrained('bert-base-uncased')
            self.tokenizers['gpt'] = AutoTokenizer.from_pretrained('gpt2')
        except Exception as e:
            logger.warning(f"Could not load transformer tokenizers: {e}")
        
        # Load spacy models
        try:
            self.nlp_en = spacy.load('en_core_web_sm')
        except OSError:
            logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp_en = None
    
    async def HealthCheck(self, request, context):
        """Health check endpoint"""
        return mcp_service_pb2.HealthCheckResponse(
            healthy=True,
            message="Tokenization Service is healthy"
        )
    
    async def TokenizeText(self, request, context):
        """Tokenize text using specified tokenizer"""
        try:
            text = request.text
            language = request.language or 'en'
            tokenizer_config = dict(request.tokenizer_config)
            tokenizer_type = tokenizer_config.get('type', 'bert')
            
            logger.info(f"Tokenizing text with {tokenizer_type} tokenizer")
            
            tokens = []
            
            if tokenizer_type in self.tokenizers:
                # Use transformer tokenizer
                tokenizer = self.tokenizers[tokenizer_type]
                encoded = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
                
                for i, (token_id, (start, end)) in enumerate(zip(encoded['input_ids'], encoded['offset_mapping'])):
                    token_text = tokenizer.decode([token_id])
                    token = mcp_service_pb2.Token(
                        text=token_text,
                        position=i,
                        attributes={
                            'token_id': str(token_id),
                            'start': str(start),
                            'end': str(end)
                        }
                    )
                    tokens.append(token)
            
            elif tokenizer_type == 'spacy' and self.nlp_en:
                # Use spaCy tokenizer
                doc = self.nlp_en(text)
                for i, token in enumerate(doc):
                    spacy_token = mcp_service_pb2.Token(
                        text=token.text,
                        position=i,
                        attributes={
                            'lemma': token.lemma_,
                            'pos': token.pos_,
                            'tag': token.tag_,
                            'is_alpha': str(token.is_alpha),
                            'is_stop': str(token.is_stop),
                            'start': str(token.idx),
                            'end': str(token.idx + len(token.text))
                        }
                    )
                    tokens.append(spacy_token)
            
            elif tokenizer_type == 'nltk':
                # Use NLTK tokenizer
                from nltk.tokenize import word_tokenize
                nltk_tokens = word_tokenize(text)
                for i, token_text in enumerate(nltk_tokens):
                    token = mcp_service_pb2.Token(
                        text=token_text,
                        position=i,
                        attributes={'tokenizer': 'nltk'}
                    )
                    tokens.append(token)
            
            else:
                # Simple whitespace tokenization
                simple_tokens = text.split()
                for i, token_text in enumerate(simple_tokens):
                    token = mcp_service_pb2.Token(
                        text=token_text,
                        position=i,
                        attributes={'tokenizer': 'simple'}
                    )
                    tokens.append(token)
            
            logger.info(f"Successfully tokenized text into {len(tokens)} tokens")
            
            return mcp_service_pb2.TokenizeResponse(
                tokens=tokens,
                success=True,
                message=f"Successfully tokenized into {len(tokens)} tokens"
            )
            
        except Exception as e:
            logger.error(f"Error tokenizing text: {str(e)}")
            return mcp_service_pb2.TokenizeResponse(
                tokens=[],
                success=False,
                message=f"Error tokenizing text: {str(e)}"
            )

async def serve():
    """Start the gRPC server"""
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    mcp_service_pb2_grpc.add_TokenizationServiceServicer_to_server(
        TokenizationServiceImpl(), server
    )
    
    listen_addr = '[::]:50052'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Tokenization Service on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
