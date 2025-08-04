import os
import glob
from typing import List, Dict, Any
from .document_processor import DocumentProcessor
from .vector_store import VectorStore

class DocumentLoader:
    """Handles loading documents from folders into vector store."""
    
    def __init__(self, doc_processor: DocumentProcessor, vector_store: VectorStore):
        self.doc_processor = doc_processor
        self.vector_store = vector_store
    
    def load_folder(self, folder_path: str) -> Dict[str, Any]:
        """Load all supported documents from a folder into vector store."""
        if not os.path.exists(folder_path):
            return {"success": False, "message": f"Folder {folder_path} does not exist"}
        
        results = {
            "success": True,
            "processed_files": [],
            "skipped_files": [],
            "total_chunks": 0,
            "errors": []
        }
        
        # Get all files in the folder
        all_files = []
        for ext in self.doc_processor.SUPPORTED_EXTENSIONS:
            pattern = os.path.join(folder_path, f"*{ext}")
            all_files.extend(glob.glob(pattern))
        
        if not all_files:
            return {
                "success": False, 
                "message": f"No supported files found in {folder_path}. Supported: {self.doc_processor.SUPPORTED_EXTENSIONS}"
            }
        
        for file_path in all_files:
            try:
                filename = os.path.basename(file_path)
                print(f"Processing {filename}...")
                
                # Check if file is supported
                if not self.doc_processor.is_supported(filename):
                    results["skipped_files"].append({"file": filename, "reason": "Unsupported format"})
                    continue
                
                # Extract text
                text = self.doc_processor.extract_text(file_path)
                if not text or not text.strip():
                    results["skipped_files"].append({"file": filename, "reason": "No text extracted"})
                    continue
                
                # Chunk text
                chunks = self.doc_processor.chunk_text(text)
                if not chunks:
                    results["skipped_files"].append({"file": filename, "reason": "No chunks created"})
                    continue
                
                # Create metadata for each chunk
                metadatas = [
                    {
                        'source': filename,
                        'chunk_index': i,
                        'file_path': file_path,
                        'loaded_from_folder': True
                    } 
                    for i in range(len(chunks))
                ]
                
                # Add to vector store
                self.vector_store.add_documents(chunks, metadatas)
                
                results["processed_files"].append({
                    "file": filename,
                    "chunks": len(chunks),
                    "text_length": len(text)
                })
                results["total_chunks"] += len(chunks)
                
                print(f"✅ {filename}: {len(chunks)} chunks added")
                
            except Exception as e:
                error_msg = f"Error processing {filename}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of vector store."""
        return {
            "document_count": self.vector_store.get_collection_count(),
            "has_documents": self.vector_store.get_collection_count() > 0
        }