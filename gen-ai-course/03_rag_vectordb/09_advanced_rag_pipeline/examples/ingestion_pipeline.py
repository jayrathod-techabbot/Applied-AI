"""
Document Ingestion Pipeline Example
Handles PDF, DOCX, PPT with multi-modal extraction
"""

import os
from typing import List, Dict
from pathlib import Path

try:
    import pymupdf  # PyMuPDF
    import docx2txt
    from langchain_community.document_loaders import PyMuPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
except ImportError:
    pass


class DocumentIngestionPipeline:
    """Production-ready document ingestion with multi-modal support"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def detect_file_type(self, file_path: str) -> str:
        """Detect document type based on extension"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.pptx': 'pptx',
            '.ppt': 'ppt',
            '.html': 'html',
            '.htm': 'html',
            '.txt': 'text'
        }
        return type_map.get(ext, 'unknown')
    
    def extract_text_pdf(self, file_path: str) -> List[Document]:
        """Extract text from PDF documents"""
        loader = PyMuPDFLoader(file_path)
        return loader.load()
    
    def extract_text_docx(self, file_path: str) -> List[Document]:
        """Extract text from DOCX documents"""
        text = docx2txt.process(file_path)
        return [Document(page_content=text, metadata={"source": file_path})]
    
    def extract_images_pdf(self, file_path: str) -> List[Dict]:
        """Extract images from PDF for captioning"""
        images = []
        doc = pymupdf.open(file_path)
        
        for page_num, page in enumerate(doc):
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Save image
                img_path = f"/tmp/page{page_num}_img{img_index}.png"
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                
                images.append({
                    "path": img_path,
                    "page": page_num,
                    "source": file_path
                })
        
        return images
    
    def extract_tables_pdf(self, file_path: str) -> List[Dict]:
        """Extract tables from PDF using pdfplumber"""
        import pdfplumber
        
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                extracted = page.extract_tables()
                for table in extracted:
                    import pandas as pd
                    df = pd.DataFrame(table[1:], columns=table[0])
                    tables.append({
                        "content": df.to_markdown(),
                        "description": f"Table with columns: {', '.join(df.columns)}",
                        "page": page_num,
                        "source": file_path
                    })
        return tables
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Apply semantic chunking to documents"""
        return self.splitter.split_documents(documents)
    
    def add_metadata(self, documents: List[Document], 
                     source_file: str, 
                     version: str = "v1.0") -> List[Document]:
        """Add comprehensive metadata to documents"""
        for i, doc in enumerate(documents):
            doc.metadata.update({
                "source_file": source_file,
                "chunk_index": i,
                "total_chunks": len(documents),
                "version": version,
                "processed_at": str(pd.Timestamp.now()) if 'pd' in dir() else None,
                "chunk_id": f"{Path(source_file).stem}_chunk_{i}"
            })
        return documents
    
    def process(self, file_path: str, version: str = "v1.0") -> Dict:
        """Complete ingestion pipeline"""
        file_type = self.detect_file_type(file_path)
        
        # Text extraction
        if file_type == "pdf":
            documents = self.extract_text_pdf(file_path)
            images = self.extract_images_pdf(file_path)
            tables = self.extract_tables_pdf(file_path)
        elif file_type == "docx":
            documents = self.extract_text_docx(file_path)
            images = []
            tables = []
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Chunking
        chunks = self.chunk_documents(documents)
        
        # Metadata
        chunks = self.add_metadata(chunks, file_path, version)
        
        # Process multi-modal content
        image_captions = []
        for img in images:
            # Would integrate with BLIP for captioning
            caption = f"[Image on page {img['page']} - caption to be generated]"
            image_captions.append(Document(
                page_content=caption,
                metadata={
                    "type": "image_caption",
                    "source_image": img["path"],
                    "page": img["page"],
                    "source_file": file_path
                }
            ))
        
        table_chunks = []
        for table in tables:
            table_chunks.append(Document(
                page_content=table["description"] + "\n\n" + table["content"],
                metadata={
                    "type": "table",
                    "page": table["page"],
                    "source_file": file_path
                }
            ))
        
        return {
            "text_chunks": chunks,
            "image_captions": image_captions,
            "tables": table_chunks,
            "stats": {
                "text_chunks": len(chunks),
                "images": len(images),
                "tables": len(tables)
            }
        }


if __name__ == "__main__":
    pipeline = DocumentIngestionPipeline(chunk_size=500, chunk_overlap=50)
    # result = pipeline.process("sample.pdf")
    # print(result["stats"])