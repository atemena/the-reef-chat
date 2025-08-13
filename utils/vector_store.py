import chromadb
import os
from typing import List, Dict, Any
from openai import OpenAI
import hashlib

class VectorStore:
    """Manages ChromaDB vector store operations."""
    
    def __init__(self, persist_directory: str = "./vector_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize OpenAI client if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]] = None) -> None:
        """Add documents to the vector store."""
        if not texts or not self.openai_client:
            return
        
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in texts]
        
        # Generate embeddings
        embeddings = self._get_embeddings(texts)
        
        # Generate unique IDs
        ids = [self._generate_id(text) for text in texts]
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.openai_client:
            return []
            
        query_embedding = self._get_embeddings([query])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        documents = []
        for i in range(len(results['documents'][0])):
            documents.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return documents
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
            
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [embedding.embedding for embedding in response.data]
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        self.client.delete_collection("documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_collection_count(self) -> int:
        """Get number of documents in collection."""
        return self.collection.count()