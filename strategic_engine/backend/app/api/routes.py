from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ..models.database import get_db, Document, QueryHistory
from ..services.document_processor import DocumentProcessor
from ..services.rag_service import RAGService

# Initialize services
document_processor = DocumentProcessor()
rag_service = RAGService()

# Create router
router = APIRouter()


@router.get("/")
async def root():
    """API status endpoint"""
    return {
        "message": "Strategic Decision Engine API",
        "status": "active",
        "version": "1.0.0"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test database connection
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Test RAG service
    try:
        rag_status = "healthy" if rag_service.test_connection() else "unhealthy"
    except Exception:
        rag_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and rag_status == "healthy" else "unhealthy",
        "database": db_status,
        "rag_service": rag_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/api/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload and process a new document"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'txt']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Supported types: PDF, DOCX, TXT"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Process document
        text, auto_document_type, metadata, chunks = document_processor.process_document(
            file_content, file.filename
        )
        
        # Use provided document type or auto-detected type
        final_document_type = document_type if document_type != "auto" else auto_document_type
        
        # Save to database
        db_document = Document(
            filename=file.filename,
            content=text,
            document_type=final_document_type,
            doc_metadata=json.dumps(doc_metadata),
            embedding_status="pending"
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Index document chunks in Pinecone
        indexing_success = rag_service.index_document_chunks(
            document_id=db_document.id,
            filename=file.filename,
            document_type=final_document_type,
            chunks=chunks
        )
        
        # Update embedding status
        db_document.embedding_status = "completed" if indexing_success else "failed"
        db.commit()
        
        return {
            "message": "Document uploaded and processed successfully",
            "document_id": db_document.id,
            "filename": file.filename,
            "document_type": final_document_type,
            "chunks_created": len(chunks),
            "embedding_status": db_document.embedding_status,
            "metadata": metadata
        }
        
    except Exception as e:
        # Clean up database entry if it was created
        if 'db_document' in locals():
            try:
                db.delete(db_document)
                db.commit()
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/api/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents"""
    try:
        documents = db.query(Document).order_by(Document.upload_date.desc()).all()
        
        document_list = []
        for doc in documents:
            metadata = json.loads(doc.doc_metadata) if doc.doc_metadata else {}
            document_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "upload_date": doc.upload_date.isoformat(),
                "embedding_status": doc.embedding_status,
                "word_count": metadata.get("word_count", 0),
                "character_count": metadata.get("character_count", 0)
            })
        
        return {
            "documents": document_list,
            "total_count": len(document_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.delete("/api/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its embeddings"""
    try:
        # Find document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from Pinecone
        rag_service.delete_document_vectors(document_id)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "filename": document.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@router.post("/api/query")
async def submit_query(
    query: str = Form(...),
    document_type_filter: Optional[str] = Form("all"),
    db: Session = Depends(get_db)
):
    """Submit a strategic question for analysis"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Generate RAG response
        rag_response = rag_service.generate_rag_response(
            query=query,
            document_type_filter=document_type_filter if document_type_filter != "all" else None
        )
        
        # Save to query history
        query_history = QueryHistory(
            query=query,
            response=rag_response["response"],
            sources=json.dumps(rag_response["sources"]),
            confidence_score=rag_response["confidence_score"]
        )
        
        db.add(query_history)
        db.commit()
        db.refresh(query_history)
        
        return {
            "query_id": query_history.id,
            "query": query,
            "response": rag_response["response"],
            "sources": rag_response["sources"],
            "confidence_score": rag_response["confidence_score"],
            "chunks_found": rag_response["chunks_found"],
            "timestamp": query_history.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/api/query-history")
async def get_query_history(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent query history"""
    try:
        queries = db.query(QueryHistory).order_by(
            QueryHistory.timestamp.desc()
        ).limit(limit).all()
        
        history_list = []
        for query in queries:
            sources = json.loads(query.sources) if query.sources else []
            history_list.append({
                "id": query.id,
                "query": query.query,
                "response": query.response[:200] + "..." if len(query.response) > 200 else query.response,
                "sources": sources,
                "confidence_score": query.confidence_score,
                "timestamp": query.timestamp.isoformat()
            })
        
        return {
            "history": history_list,
            "total_count": len(history_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving query history: {str(e)}")


@router.get("/api/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        # Database stats
        total_documents = db.query(Document).count()
        total_queries = db.query(QueryHistory).count()
        
        # Document type distribution
        doc_types = db.query(Document.document_type, db.func.count(Document.id)).group_by(
            Document.document_type
        ).all()
        
        doc_type_stats = {doc_type: count for doc_type, count in doc_types}
        
        # Pinecone stats
        pinecone_stats = rag_service.get_index_stats()
        
        return {
            "total_documents": total_documents,
            "total_queries": total_queries,
            "document_types": doc_type_stats,
            "pinecone_stats": pinecone_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


# Include router in main app
def get_router():
    return router