from typing import List, Dict, Any, Optional, Union
import re
import uuid
from io import BytesIO
import PyPDF2
from docx import Document
from loguru import logger
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter
)
from llama_index.text_splitter import SentenceSplitter, TokenTextSplitter as LITokenTextSplitter
import tiktoken
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

from ..models import (
    ChunkingRequest, ChunkingResponse, ChunkingMethod, 
    DocumentType, ChunkMetadata
)
from ..config import settings


class ChunkingHandler:
    def __init__(self):
        self._initialize_nltk()
        self._text_splitters = {}
    
    def _initialize_nltk(self):
        """Initialize NLTK data"""
        try:
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
            
            nltk.download('punkt', quiet=True)
            logger.info("NLTK data initialized successfully")
        except Exception as e:
            logger.warning(f"Could not download NLTK data: {e}")
    
    async def chunk_content(self, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk content based on the specified method"""
        try:
            # Extract text from content based on document type
            text_content = await self._extract_text(request.content, request.document_type)
            
            # Validate content size
            if len(text_content) > settings.max_content_size:
                raise ValueError(f"Content too large: {len(text_content)} characters (max: {settings.max_content_size})")
            
            # Choose chunking method
            if request.method == ChunkingMethod.FIXED_SIZE:
                return await self._chunk_fixed_size(text_content, request)
            elif request.method == ChunkingMethod.RECURSIVE:
                return await self._chunk_recursive(text_content, request)
            elif request.method == ChunkingMethod.SEMANTIC:
                return await self._chunk_semantic(text_content, request)
            elif request.method == ChunkingMethod.SENTENCE_BASED:
                return await self._chunk_sentence_based(text_content, request)
            elif request.method == ChunkingMethod.PARAGRAPH_BASED:
                return await self._chunk_paragraph_based(text_content, request)
            elif request.method == ChunkingMethod.TOKEN_BASED:
                return await self._chunk_token_based(text_content, request)
            elif request.method == ChunkingMethod.DOCUMENT_BASED:
                return await self._chunk_document_based(text_content, request)
            else:
                raise ValueError(f"Unsupported chunking method: {request.method}")
                
        except Exception as e:
            logger.error(f"Error in chunk_content: {e}")
            raise
    
    async def _extract_text(self, content: Union[str, bytes], doc_type: DocumentType) -> str:
        """Extract text content based on document type"""
        if doc_type == DocumentType.TEXT:
            return content if isinstance(content, str) else content.decode('utf-8')
        
        elif doc_type == DocumentType.PDF:
            return await self._extract_pdf_text(content)
        
        elif doc_type == DocumentType.DOCX:
            return await self._extract_docx_text(content)
        
        elif doc_type == DocumentType.HTML:
            return await self._extract_html_text(content)
        
        elif doc_type == DocumentType.MARKDOWN:
            # For markdown, we can treat it as text initially
            text_content = content if isinstance(content, str) else content.decode('utf-8')
            return text_content
        
        else:
            # Default to text extraction
            return content if isinstance(content, str) else content.decode('utf-8')
    
    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            pdf_file = BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
    
    async def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX content"""
        try:
            docx_file = BytesIO(content)
            doc = Document(docx_file)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise
    
    async def _extract_html_text(self, content: Union[str, bytes]) -> str:
        """Extract text from HTML content"""
        try:
            from bs4 import BeautifulSoup
            
            html_content = content if isinstance(content, str) else content.decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting HTML text: {e}")
            # Fallback to simple text extraction
            html_content = content if isinstance(content, str) else content.decode('utf-8')
            return re.sub(r'<[^>]+>', '', html_content)
    
    async def _chunk_fixed_size(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text using fixed size method"""
        chunks = []
        metadata = []
        
        for i in range(0, len(text), request.chunk_size - request.chunk_overlap):
            start_index = i
            end_index = min(i + request.chunk_size, len(text))
            chunk = text[start_index:end_index]
            
            if len(chunk.strip()) >= request.min_chunk_size:
                chunks.append(chunk)
                metadata.append(ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    start_index=start_index,
                    end_index=end_index,
                    chunk_size=len(chunk)
                ))
        
        return ChunkingResponse(
            chunks=chunks,
            metadata=metadata,
            total_chunks=len(chunks),
            total_characters=len(text),
            method_used=request.method,
            processing_info={"chunk_size": request.chunk_size, "overlap": request.chunk_overlap}
        )
    
    async def _chunk_recursive(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text using recursive character text splitter"""
        separators = request.separators or ["\n\n", "\n", " ", ""]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            separators=separators
        )
        
        chunks = text_splitter.split_text(text)
        metadata = []
        
        current_index = 0
        for i, chunk in enumerate(chunks):
            start_index = text.find(chunk, current_index)
            end_index = start_index + len(chunk)
            
            metadata.append(ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                start_index=start_index,
                end_index=end_index,
                chunk_size=len(chunk)
            ))
            
            current_index = start_index + 1
        
        return ChunkingResponse(
            chunks=chunks,
            metadata=metadata,
            total_chunks=len(chunks),
            total_characters=len(text),
            method_used=request.method,
            processing_info={"separators": separators}
        )
    
    async def _chunk_semantic(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text using semantic-based splitting with LlamaIndex"""
        try:
            splitter = SentenceSplitter(
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap
            )
            
            chunks = splitter.split_text(text)
            metadata = []
            
            current_index = 0
            for chunk in chunks:
                start_index = text.find(chunk, current_index)
                end_index = start_index + len(chunk)
                
                metadata.append(ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    start_index=start_index,
                    end_index=end_index,
                    chunk_size=len(chunk)
                ))
                
                current_index = start_index + 1
            
            return ChunkingResponse(
                chunks=chunks,
                metadata=metadata,
                total_chunks=len(chunks),
                total_characters=len(text),
                method_used=request.method,
                processing_info={"framework": "llamaindex"}
            )
        except Exception as e:
            logger.error(f"Error in semantic chunking: {e}")
            # Fallback to recursive chunking
            return await self._chunk_recursive(text, request)
    
    async def _chunk_sentence_based(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text based on sentences"""
        try:
            sentences = sent_tokenize(text)
        except Exception:
            # Fallback sentence splitting
            sentences = re.split(r'[.!?]+\s+', text)
        
        chunks = []
        metadata = []
        current_chunk = ""
        start_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= request.chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    end_index = start_index + len(current_chunk)
                    chunks.append(current_chunk)
                    metadata.append(ChunkMetadata(
                        chunk_id=str(uuid.uuid4()),
                        start_index=start_index,
                        end_index=end_index,
                        chunk_size=len(current_chunk)
                    ))
                    start_index = end_index
                
                current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            end_index = start_index + len(current_chunk)
            chunks.append(current_chunk)
            metadata.append(ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                start_index=start_index,
                end_index=end_index,
                chunk_size=len(current_chunk)
            ))
        
        return ChunkingResponse(
            chunks=chunks,
            metadata=metadata,
            total_chunks=len(chunks),
            total_characters=len(text),
            method_used=request.method,
            processing_info={"sentence_count": len(sentences)}
        )
    
    async def _chunk_paragraph_based(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text based on paragraphs"""
        paragraphs = text.split('\n\n')
        chunks = []
        metadata = []
        current_chunk = ""
        start_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            if len(current_chunk) + len(paragraph) <= request.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    end_index = start_index + len(current_chunk)
                    chunks.append(current_chunk)
                    metadata.append(ChunkMetadata(
                        chunk_id=str(uuid.uuid4()),
                        start_index=start_index,
                        end_index=end_index,
                        chunk_size=len(current_chunk)
                    ))
                    start_index = end_index
                
                current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            end_index = start_index + len(current_chunk)
            chunks.append(current_chunk)
            metadata.append(ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                start_index=start_index,
                end_index=end_index,
                chunk_size=len(current_chunk)
            ))
        
        return ChunkingResponse(
            chunks=chunks,
            metadata=metadata,
            total_chunks=len(chunks),
            total_characters=len(text),
            method_used=request.method,
            processing_info={"paragraph_count": len(paragraphs)}
        )
    
    async def _chunk_token_based(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text based on token count"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            
            text_splitter = TokenTextSplitter(
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                encoding_name="cl100k_base"
            )
            
            chunks = text_splitter.split_text(text)
            metadata = []
            
            current_index = 0
            for chunk in chunks:
                start_index = text.find(chunk, current_index)
                end_index = start_index + len(chunk)
                token_count = len(encoding.encode(chunk))
                
                metadata.append(ChunkMetadata(
                    chunk_id=str(uuid.uuid4()),
                    start_index=start_index,
                    end_index=end_index,
                    chunk_size=len(chunk),
                    token_count=token_count
                ))
                
                current_index = start_index + 1
            
            return ChunkingResponse(
                chunks=chunks,
                metadata=metadata,
                total_chunks=len(chunks),
                total_characters=len(text),
                method_used=request.method,
                processing_info={"encoding": "cl100k_base"}
            )
        except Exception as e:
            logger.error(f"Error in token-based chunking: {e}")
            # Fallback to fixed size chunking
            return await self._chunk_fixed_size(text, request)
    
    async def _chunk_document_based(self, text: str, request: ChunkingRequest) -> ChunkingResponse:
        """Chunk text based on document structure (headers, sections)"""
        # Simple implementation - split on headers
        header_pattern = r'^#{1,6}\s+(.+)$'
        lines = text.split('\n')
        chunks = []
        metadata = []
        current_chunk = ""
        current_title = None
        start_index = 0
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Found a header, save previous chunk
                if current_chunk.strip():
                    end_index = start_index + len(current_chunk)
                    chunks.append(current_chunk.strip())
                    metadata.append(ChunkMetadata(
                        chunk_id=str(uuid.uuid4()),
                        start_index=start_index,
                        end_index=end_index,
                        chunk_size=len(current_chunk.strip()),
                        section_title=current_title,
                        hierarchy_level=len(header_match.group(0)) - len(header_match.group(0).lstrip('#'))
                    ))
                    start_index = end_index
                
                current_title = header_match.group(1)
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        # Add final chunk
        if current_chunk.strip():
            end_index = start_index + len(current_chunk)
            chunks.append(current_chunk.strip())
            metadata.append(ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                start_index=start_index,
                end_index=end_index,
                chunk_size=len(current_chunk.strip()),
                section_title=current_title
            ))
        
        return ChunkingResponse(
            chunks=chunks,
            metadata=metadata,
            total_chunks=len(chunks),
            total_characters=len(text),
            method_used=request.method,
            processing_info={"structure_based": True}
        )
