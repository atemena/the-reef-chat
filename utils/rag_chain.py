from openai import OpenAI
import os
from typing import Generator
from .document_processor import DocumentProcessor

class CAGChain:
    """Cache-Augmented Generation pipeline for single PDF."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.document_content = None
        
        # Initialize OpenAI client if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
            
        self.system_message = """You are a helpful AI assistant that answers questions based on the cached PDF document content. 
Use the document content to answer the user's question accurately and concisely. 
If the document doesn't contain enough information to answer the question, say so clearly.
Always base your answers on the provided document content."""
        
        # Cache the PDF content on initialization
        self._cache_document()
    
    def _cache_document(self):
        """Cache the PDF document content for reuse."""
        if os.path.exists(self.pdf_path):
            doc_processor = DocumentProcessor()
            self.document_content = doc_processor.extract_text(self.pdf_path)
            print(f"✅ Cached PDF content: {len(self.document_content)} characters")
        else:
            self.document_content = None
            print(f"❌ PDF not found at: {self.pdf_path}")
    
    def generate_response(self, query: str, stream: bool = True) -> Generator[str, None, None]:
        """Generate response using Cache-Augmented Generation."""
        if not self.openai_client:
            yield "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
            return
            
        if not self.document_content:
            yield "Error: No document cached or document could not be processed."
            return
        
        # Create prompt with cached document content
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": f"Document Content:\n{self.document_content}\n\nQuestion: {query}"}
        ]
        
        # Generate response
        if stream:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            yield response.choices[0].message.content
    
    def has_document(self) -> bool:
        """Check if document is loaded."""
        return self.document_content is not None and len(self.document_content.strip()) > 0