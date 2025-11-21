"""
Document Loader Service - Handles loading and processing of various document formats
"""
import logging
from typing import List, Dict, Any
from pathlib import Path

from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
    CSVLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.schema import Document

from app.config import settings

logger = logging.getLogger(__name__)

class DocumentLoader:
    """Service for loading and processing documents"""
    
    def __init__(self):
        """Initialize document loader with text splitter"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Map file extensions to loaders
        self.loader_mapping = {
            '.pdf': self._load_pdf,
            '.txt': self._load_text,
            '.docx': self._load_docx,
            '.doc': self._load_docx,
            '.md': self._load_markdown,
            '.csv': self._load_csv
        }
    
    def load_documents(self, directory_path: str) -> List[Document]:
        """
        Load all documents from a directory
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of processed document chunks
        """
        documents = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.warning(f"Directory {directory_path} does not exist")
            return documents
        
        # Process each file in the directory
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    file_docs = self.load_single_document(str(file_path))
                    documents.extend(file_docs)
                    logger.info(f"Loaded {len(file_docs)} chunks from {file_path.name}")
                except Exception as e:
                    logger.error(f"Error loading {file_path.name}: {str(e)}")
        
        logger.info(f"Total documents loaded from {directory_path}: {len(documents)}")
        return documents
    
    def load_single_document(self, file_path: str) -> List[Document]:
        """
        Load and process a single document
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of document chunks
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise ValueError(f"File {file_path} does not exist")
        
        # Get file extension
        file_ext = file_path_obj.suffix.lower()
        
        # Get appropriate loader
        loader_func = self.loader_mapping.get(file_ext)
        
        if not loader_func:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        try:
            # Load document
            raw_documents = loader_func(file_path)
            
            # Add metadata
            for doc in raw_documents:
                doc.metadata.update({
                    'source': file_path,
                    'filename': file_path_obj.name,
                    'file_type': file_ext
                })
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(raw_documents)
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF document"""
        try:
            loader = PyPDFLoader(file_path)
            return loader.load()
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {str(e)}")
            # Fallback to unstructured loader
            loader = UnstructuredPDFLoader(file_path)
            return loader.load()
    
    def _load_text(self, file_path: str) -> List[Document]:
        """Load text document"""
        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()
    
    def _load_docx(self, file_path: str) -> List[Document]:
        """Load Word document"""
        loader = UnstructuredWordDocumentLoader(file_path)
        return loader.load()
    
    def _load_markdown(self, file_path: str) -> List[Document]:
        """Load Markdown document"""
        loader = UnstructuredMarkdownLoader(file_path)
        return loader.load()
    
    def _load_csv(self, file_path: str) -> List[Document]:
        """Load CSV document"""
        loader = CSVLoader(file_path, encoding='utf-8')
        return loader.load()
    
    def process_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Process raw text into document chunks
        
        Args:
            text: Raw text to process
            metadata: Optional metadata to add to documents
            
        Returns:
            List of document chunks
        """
        # Create document
        document = Document(
            page_content=text,
            metadata=metadata or {}
        )
        
        # Split into chunks
        chunks = self.text_splitter.split_documents([document])
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks)
            })
        
        return chunks
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return list(self.loader_mapping.keys())
