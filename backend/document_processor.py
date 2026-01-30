from PyPDF2 import PdfReader
from docx import Document
from typing import List, Dict
import io

class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        pdf_reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def process_document(self, file_content: bytes, filename: str) -> List[Dict[str, str]]:
        if filename.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_content)
        elif filename.lower().endswith('.docx'):
            text = self.extract_text_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        chunks = self.chunk_text(text)
        
        return [
            {
                'text': chunk,
                'source': filename,
                'page': i
            }
            for i, chunk in enumerate(chunks)
        ]

doc_processor = DocumentProcessor()
