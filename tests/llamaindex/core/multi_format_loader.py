import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.readers.file import PDFReader, DocxReader
import mimetypes
import chardet


class MultiFormatLoader:
    """複数フォーマットのドキュメントを読み込むクラス"""
    
    def __init__(self):
        self.supported_extensions = {
            '.txt': self._load_text,
            '.md': self._load_text,
            '.pdf': self._load_pdf,
            '.docx': self._load_docx,
            '.doc': self._load_docx,
            '.html': self._load_html,
            '.json': self._load_json,
            '.csv': self._load_csv
        }
        
    def load_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """単一ドキュメントを読み込み"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension not in self.supported_extensions:
            raise ValueError(f"サポートされていないファイル形式: {extension}")
        
        # メタデータの基本情報を設定
        base_metadata = {
            "file_name": path.name,
            "file_path": str(path.absolute()),
            "file_size": path.stat().st_size,
            "file_type": extension,
            "mime_type": mimetypes.guess_type(str(path))[0]
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        # ファイル形式に応じて読み込み
        loader_func = self.supported_extensions[extension]
        documents = loader_func(str(path))
        
        # メタデータを各ドキュメントに追加
        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata.update(base_metadata)
        
        return documents
    
    def load_directory(self, directory_path: str, recursive: bool = True, 
                      metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """ディレクトリ内のドキュメントを一括読み込み"""
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            raise ValueError(f"ディレクトリが見つかりません: {directory_path}")
        
        all_documents = []
        
        # ファイルを再帰的に検索
        pattern = "**/*" if recursive else "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    documents = self.load_document(str(file_path), metadata)
                    all_documents.extend(documents)
                except Exception as e:
                    print(f"ファイル読み込みエラー {file_path}: {e}")
                    continue
        
        return all_documents
    
    def _load_text(self, file_path: str) -> List[Document]:
        """テキストファイルを読み込み"""
        try:
            # エンコーディング自動検出
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result['encoding'] or 'utf-8'
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            return [Document(text=content)]
        except Exception as e:
            print(f"テキストファイル読み込みエラー: {e}")
            return []
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """PDFファイルを読み込み"""
        try:
            pdf_reader = PDFReader()
            documents = pdf_reader.load_data(file_path)
            return documents
        except Exception as e:
            print(f"PDF読み込みエラー: {e}")
            return []
    
    def _load_docx(self, file_path: str) -> List[Document]:
        """Word文書を読み込み"""
        try:
            docx_reader = DocxReader()
            documents = docx_reader.load_data(file_path)
            return documents
        except Exception as e:
            print(f"Word文書読み込みエラー: {e}")
            return []
    
    def _load_html(self, file_path: str) -> List[Document]:
        """HTMLファイルを読み込み"""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # スクリプトとスタイルを除去
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            # 複数の改行を単一化
            text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
            
            return [Document(text=text)]
        except Exception as e:
            print(f"HTML読み込みエラー: {e}")
            return []
    
    def _load_json(self, file_path: str) -> List[Document]:
        """JSONファイルを読み込み"""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # JSONを文字列として保存
            text = json.dumps(data, ensure_ascii=False, indent=2)
            
            return [Document(text=text)]
        except Exception as e:
            print(f"JSON読み込みエラー: {e}")
            return []
    
    def _load_csv(self, file_path: str) -> List[Document]:
        """CSVファイルを読み込み"""
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            
            # CSVの内容を文字列に変換
            text = df.to_string(index=False)
            
            return [Document(text=text)]
        except Exception as e:
            print(f"CSV読み込みエラー: {e}")
            return []
    
    def get_supported_formats(self) -> List[str]:
        """サポートされているファイル形式一覧を取得"""
        return list(self.supported_extensions.keys())
    
    def validate_file(self, file_path: str) -> bool:
        """ファイルが読み込み可能かチェック"""
        path = Path(file_path)
        return (path.exists() and 
                path.is_file() and 
                path.suffix.lower() in self.supported_extensions)