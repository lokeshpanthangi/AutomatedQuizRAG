import os
import re
from datetime import datetime
from typing import List, Dict, Tuple
from io import BytesIO

# Document processing imports
import PyPDF2
from docx import Document as DocxDocument


class DocumentProcessor:
    """Service for processing uploaded documents"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
        
        # Keywords for document classification
        self.classification_keywords = {
            'financial': ['revenue', 'profit', 'budget', 'financial', 'income', 'expense', 'balance sheet', 'cash flow', 'roi', 'investment'],
            'market_research': ['market', 'research', 'survey', 'analysis', 'competitor', 'customer', 'trend', 'demographic', 'segment'],
            'internal': ['employee', 'hr', 'human resources', 'policy', 'procedure', 'internal', 'staff', 'team', 'organization']
        }
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text from uploaded file based on file extension"""
        file_extension = os.path.splitext(filename)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_content)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_content)
            elif file_extension == '.txt':
                return self._extract_from_txt(file_content)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            raise Exception(f"Error extracting text from {filename}: {str(e)}")
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        text = ""
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        text = ""
        docx_file = BytesIO(file_content)
        doc = DocxDocument(docx_file)
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    
    def _extract_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            return file_content.decode('latin-1')
    
    def extract_metadata(self, filename: str, content: str) -> Dict:
        """Extract metadata from document"""
        word_count = len(content.split())
        char_count = len(content)
        
        doc_metadata = {
            'word_count': word_count,
            'character_count': char_count,
            'file_size_chars': char_count,
            'extraction_date': datetime.utcnow().isoformat()
        }
        
        return doc_metadata
    
    def classify_document(self, filename: str, content: str) -> str:
        """Auto-classify document based on filename and content keywords"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Count keyword matches for each category
        category_scores = {}
        
        for category, keywords in self.classification_keywords.items():
            score = 0
            
            # Check filename
            for keyword in keywords:
                if keyword in filename_lower:
                    score += 2  # Filename matches get higher weight
                
                # Check content (limit to first 1000 characters for efficiency)
                content_sample = content_lower[:1000]
                score += content_sample.count(keyword)
            
            category_scores[category] = score
        
        # Return category with highest score, default to 'general'
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks with overlap, breaking at sentence boundaries when possible"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = start + chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:].strip())
                break
            
            # Try to break at sentence boundary
            chunk_text = text[start:end]
            
            # Look for sentence endings near the end of the chunk
            sentence_endings = ['.', '!', '?', '\n']
            best_break = -1
            
            # Search backwards from the end for a good break point
            for i in range(len(chunk_text) - 1, max(0, len(chunk_text) - 200), -1):
                if chunk_text[i] in sentence_endings and i < len(chunk_text) - 1:
                    if chunk_text[i + 1].isspace() or chunk_text[i + 1].isupper():
                        best_break = i + 1
                        break
            
            if best_break > 0:
                # Break at sentence boundary
                chunk = text[start:start + best_break].strip()
                chunks.append(chunk)
                start = start + best_break - overlap
            else:
                # No good break point found, break at chunk_size
                chunk = text[start:end].strip()
                chunks.append(chunk)
                start = end - overlap
            
            # Ensure we don't go backwards
            if start < 0:
                start = 0
        
        # Remove empty chunks
        chunks = [chunk for chunk in chunks if chunk.strip()]
        
        return chunks
    
    def process_document(self, file_content: bytes, filename: str) -> Tuple[str, str, Dict, List[str]]:
        """Complete document processing pipeline"""
        # Extract text
        text = self.extract_text_from_file(file_content, filename)
        
        if not text.strip():
            raise ValueError("No text could be extracted from the document")
        
        # Extract metadata
        doc_metadata = self.extract_metadata(filename, text)
        
        # Classify document
        document_type = self.classify_document(filename, text)
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        return text, document_type, doc_metadata, chunks


# Example usage and testing
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # Test text chunking
    sample_text = "This is a sample document. It contains multiple sentences. Each sentence should be preserved when possible. The chunking algorithm should break at sentence boundaries when feasible."
    chunks = processor.chunk_text(sample_text, chunk_size=50, overlap=10)
    
    print("Sample chunks:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1}: {chunk}")
    
    # Test classification
    test_content = "This document contains financial information about revenue and profit margins."
    classification = processor.classify_document("financial_report.pdf", test_content)
    print(f"\nClassification: {classification}")
    
    print("\nDocument processor initialized successfully!")