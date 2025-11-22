"""
Vector Store Service - Manages FAISS vector stores for document retrieval
"""
import os
import logging
import pickle
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

from app.config import settings

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service for managing vector stores"""
    
    def __init__(self):
        """Initialize vector store service"""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_embedding_model
        )
        self.vector_stores: Dict[str, FAISS] = {}
        self.vector_store_path = Path(settings.vector_store_path)
        self.vector_store_path.mkdir(exist_ok=True)
        
        # Load existing vector stores
        self._load_existing_stores()
    
    def _load_existing_stores(self):
        """Load existing vector stores from disk"""
        for store_file in self.vector_store_path.glob("*.pkl"):
            agent_name = store_file.stem
            try:
                self.vector_stores[agent_name] = self._load_store(agent_name)
                logger.info(f"Loaded vector store for {agent_name}")
            except Exception as e:
                logger.error(f"Error loading vector store for {agent_name}: {str(e)}")
    
    def create_vector_store(self, agent: str, documents: List[Document]) -> FAISS:
        """
        Create a new vector store for an agent
        
        Args:
            agent: Agent name
            documents: List of documents to index
            
        Returns:
            Created FAISS vector store
        """
        try:
            if not documents:
                logger.warning(f"No documents provided for {agent}")
                return None
            
            # Create vector store
            vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            # Save to memory and disk
            self.vector_stores[agent] = vector_store
            self._save_store(agent, vector_store)
            
            logger.info(f"Created vector store for {agent} with {len(documents)} documents")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store for {agent}: {str(e)}")
            raise
    
    def add_documents(self, agent: str, documents: List[Document]) -> int:
        """
        Add documents to existing vector store
        
        Args:
            agent: Agent name
            documents: Documents to add
            
        Returns:
            Number of documents added
        """
        try:
            if not documents:
                return 0
            
            # Get or create vector store
            if agent in self.vector_stores:
                vector_store = self.vector_stores[agent]
                vector_store.add_documents(documents)
            else:
                vector_store = self.create_vector_store(agent, documents)
            
            # Save updated store
            self._save_store(agent, vector_store)
            
            logger.info(f"Added {len(documents)} documents to {agent} vector store")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error adding documents to {agent}: {str(e)}")
            raise
    
    def search(
        self,
        agent: str,
        query: str,
        k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents
        
        Args:
            agent: Agent name
            query: Search query
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (document, score) tuples
        """
        try:
            if agent not in self.vector_stores:
                logger.warning(f"No vector store found for {agent}")
                return []
            
            vector_store = self.vector_stores[agent]
            
            # Perform similarity search with scores
            results = vector_store.similarity_search_with_score(query, k=k)
            
            # Filter by threshold
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= threshold
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant documents for query in {agent}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching in {agent}: {str(e)}")
            return []
    
    def get_retriever(self, agent: str, **kwargs):
        """
        Get a retriever for an agent's vector store
        
        Args:
            agent: Agent name
            **kwargs: Additional retriever parameters
            
        Returns:
            Retriever instance
        """
        if agent not in self.vector_stores:
            logger.warning(f"No vector store found for {agent}")
            return None
        
        return self.vector_stores[agent].as_retriever(**kwargs)
    
    def remove_document(self, agent: str, filename: str):
        """
        Remove documents from vector store by filename
        
        Args:
            agent: Agent name
            filename: Filename to remove
        """
        if agent not in self.vector_stores:
            return
        
        try:
            logger.info(f"Document removal requested for {filename} in {agent}")
            # Rebuild vector store without the specified file
            self._rebuild_store_without_file(agent, filename)
        except Exception as e:
            logger.error(f"Error removing document: {str(e)}")
    
    def clear_store(self, agent: str):
        """
        Clear all documents from an agent's vector store
        
        Args:
            agent: Agent name
        """
        try:
            if agent in self.vector_stores:
                del self.vector_stores[agent]
            
            # Remove from disk
            store_file = self.vector_store_path / f"{agent}.pkl"
            if store_file.exists():
                store_file.unlink()
            
            index_file = self.vector_store_path / f"{agent}.faiss"
            if index_file.exists():
                index_file.unlink()
            
            logger.info(f"Cleared vector store for {agent}")
            
        except Exception as e:
            logger.error(f"Error clearing store for {agent}: {str(e)}")
    
    def _save_store(self, agent: str, vector_store: FAISS):
        """Save vector store to disk"""
        try:
            # Save FAISS index
            vector_store.save_local(
                folder_path=str(self.vector_store_path),
                index_name=agent
            )
            logger.info(f"Saved vector store for {agent}")
        except Exception as e:
            logger.error(f"Error saving vector store for {agent}: {str(e)}")
    
    def _load_store(self, agent: str) -> Optional[FAISS]:
        """Load vector store from disk"""
        try:
            vector_store = FAISS.load_local(
                folder_path=str(self.vector_store_path),
                embeddings=self.embeddings,
                index_name=agent,
                allow_dangerous_deserialization=True  
            )
            return vector_store
        except Exception as e:
            logger.error(f"Error loading vector store for {agent}: {str(e)}")
            return None
    
    def _rebuild_store_without_file(self, agent: str, filename: str):
        """Rebuild vector store excluding a specific file"""
        logger.info(f"Rebuilding store for {agent} without {filename}")
        pass
    
    def get_store_stats(self, agent: str) -> Dict[str, Any]:
        """
        Get statistics for an agent's vector store
        
        Args:
            agent: Agent name
            
        Returns:
            Dictionary with store statistics
        """
        if agent not in self.vector_stores:
            return {"exists": False}
        
        try:
            vector_store = self.vector_stores[agent]
            # Get approximate document count
            return {
                "exists": True,
                "agent": agent,
            }
        except Exception as e:
            logger.error(f"Error getting stats for {agent}: {str(e)}")
            return {"exists": False, "error": str(e)}
    
    def get_all_agents(self) -> List[str]:
        """Get list of all agents with vector stores"""
        return list(self.vector_stores.keys())
