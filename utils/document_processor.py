import os
import PyPDF2
import docx
from typing import List, Optional

class DocumentProcessor:
    """Handles file parsing and text extraction."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx'}
    
    def __init__(self):
        pass
    
    def is_supported(self, filename: str) -> bool:
        """Check if file type is supported."""
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.SUPPORTED_EXTENSIONS
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from supported file types."""
        if not os.path.exists(file_path):
            return None
        
        ext = os.path.splitext(file_path.lower())[1]
        
        try:
            if ext == '.txt':
                return self._extract_from_txt(file_path)
            elif ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif ext == '.docx':
                return self._extract_from_docx(file_path)
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return None
        
        return None
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from .txt files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from .pdf files."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from .docx files."""
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [chunk for chunk in chunks if chunk]