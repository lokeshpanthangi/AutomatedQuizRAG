import os
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import logging
import uuid
import json

from .openai_service import OpenAIService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval Augmented Generation) service using Pinecone and OpenAI"""
    
    def __init__(self):
        # Initialize Pinecone
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "strategic-docs")
        
        # Initialize Pinecone only if API key is available
        self.pc = None
        if self.pinecone_api_key and self.pinecone_api_key != "your_actual_pinecone_api_key":
            try:
                self.pc = Pinecone(api_key=self.pinecone_api_key)
                logger.info("Pinecone initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {str(e)}")
                self.pc = None
        else:
            logger.warning("Pinecone API key not configured - vector search will be disabled")
        
        # Initialize OpenAI service
        self.openai_service = OpenAIService()
        
        # Vector dimension for OpenAI embeddings
        self.vector_dimension = 1536
        
        # Initialize index (will be created if it doesn't exist)
        self.index = None
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize Pinecone index"""
        if not self.pc:
            logger.warning("Pinecone not initialized - skipping index initialization")
            return
            
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.vector_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Index {self.index_name} created successfully")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {str(e)}")
            self.index = None
    
    def index_document_chunks(self, document_id: int, filename: str, document_type: str, chunks: List[str]) -> bool:
        """Index document chunks in Pinecone"""
        if not self.index:
            logger.warning("Pinecone index not available - skipping vector indexing")
            return False
            
        try:
            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks from {filename}")
            embeddings = self.openai_service.generate_embeddings_batch(chunks)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"doc_{document_id}_chunk_{i}"
                
                metadata = {
                    "document_id": document_id,
                    "filename": filename,
                    "document_type": document_type,
                    "chunk_index": i,
                    "text": chunk[:1000],  # Limit text in metadata
                    "chunk_length": len(chunk)
                }
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert vectors in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
            
            logger.info(f"Successfully indexed {len(chunks)} chunks for document {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document chunks: {str(e)}")
            return False
    
    def search_similar_chunks(self, query: str, top_k: int = 5, document_type_filter: Optional[str] = None) -> List[Dict]:
        """Search for similar chunks based on query embedding"""
        if not self.index:
            logger.warning("Pinecone index not available - returning empty results")
            return []
            
        try:
            # Generate query embedding
            query_embedding = self.openai_service.generate_embedding(query)
            
            # Prepare filter
            filter_dict = {}
            if document_type_filter and document_type_filter != "all":
                filter_dict["document_type"] = document_type_filter
            
            # Search in Pinecone
            search_kwargs = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": True
            }
            
            if filter_dict:
                search_kwargs["filter"] = filter_dict
            
            results = self.index.query(**search_kwargs)
            
            # Process results
            similar_chunks = []
            for match in results.matches:
                chunk_data = {
                    "id": match.id,
                    "score": float(match.score),
                    "text": match.metadata.get("text", ""),
                    "document_id": match.metadata.get("document_id"),
                    "filename": match.metadata.get("filename"),
                    "document_type": match.metadata.get("document_type"),
                    "chunk_index": match.metadata.get("chunk_index")
                }
                similar_chunks.append(chunk_data)
            
            logger.info(f"Found {len(similar_chunks)} similar chunks for query")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    def delete_document_vectors(self, document_id: int) -> bool:
        """Delete all vectors for a specific document"""
        if not self.index:
            logger.warning("Pinecone index not available - skipping vector deletion")
            return False
            
        try:
            # Query to find all vectors for this document
            filter_dict = {"document_id": document_id}
            
            # Get all vector IDs for this document
            query_response = self.index.query(
                vector=[0.0] * self.vector_dimension,  # Dummy vector
                top_k=10000,  # Large number to get all
                filter=filter_dict,
                include_metadata=False
            )
            
            # Extract vector IDs
            vector_ids = [match.id for match in query_response.matches]
            
            if vector_ids:
                # Delete vectors
                self.index.delete(ids=vector_ids)
                logger.info(f"Deleted {len(vector_ids)} vectors for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document vectors: {str(e)}")
            return False
    
    def generate_rag_response(self, query: str, document_type_filter: Optional[str] = None) -> Dict:
        """Generate complete RAG response with context and sources"""
        try:
            # Analyze query intent
            intent_analysis = self.openai_service.analyze_query_intent(query)
            
            # Search for relevant chunks
            similar_chunks = self.search_similar_chunks(
                query=query,
                top_k=5,
                document_type_filter=document_type_filter
            )
            
            if not similar_chunks:
                return {
                    "response": "I couldn't find relevant information in the uploaded documents to answer your question. Please ensure you have uploaded relevant documents or try rephrasing your question.",
                    "sources": [],
                    "confidence_score": "0.0",
                    "chunks_found": 0
                }
            
            # Prepare context and sources
            context_chunks = []
            sources = set()
            total_score = 0
            
            for chunk in similar_chunks:
                context_chunks.append({
                    "text": chunk["text"],
                    "score": chunk["score"],
                    "source": chunk["filename"]
                })
                sources.add(chunk["filename"])
                total_score += chunk["score"]
            
            # Calculate average confidence score
            avg_confidence = total_score / len(similar_chunks) if similar_chunks else 0
            
            # Generate strategic response
            response = self.openai_service.generate_strategic_response(
                query=query,
                context_chunks=context_chunks,
                sources=list(sources)
            )
            
            return {
                "response": response,
                "sources": list(sources),
                "confidence_score": f"{avg_confidence:.3f}",
                "chunks_found": len(similar_chunks),
                "intent_analysis": intent_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return {
                "response": f"I encountered an error while processing your question: {str(e)}. Please try again.",
                "sources": [],
                "confidence_score": "0.0",
                "chunks_found": 0
            }
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the Pinecone index"""
        if not self.index:
            return {"error": "Index not available", "total_vectors": 0}
            
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {"error": str(e), "total_vectors": 0}
    
    def test_connection(self) -> bool:
        """Test Pinecone connection"""
        if not self.index:
            logger.warning("Pinecone index not available")
            return False
            
        try:
            stats = self.index.describe_index_stats()
            return True
        except Exception as e:
            logger.error(f"Pinecone connection test failed: {str(e)}")
            return False


# Example usage and testing
if __name__ == "__main__":
    try:
        rag_service = RAGService()
        
        # Test connection
        if rag_service.test_connection():
            print("✅ Pinecone connection successful!")
        else:
            print("❌ Pinecone connection failed!")
        
        # Get index stats
        stats = rag_service.get_index_stats()
        print(f"✅ Index stats: {stats}")
        
        print("\nRAG service initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing RAG service: {str(e)}")
        print("Please check your Pinecone configuration in the .env file")