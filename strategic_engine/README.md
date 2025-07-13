# 🎯 Strategic Decision Engine

An AI-powered strategic planning platform for CEOs and executives. Upload company documents and get intelligent strategic insights through a RAG (Retrieval Augmented Generation) system.

## 🌟 Features

- **Document Upload & Processing**: Support for PDF, DOCX, and TXT files
- **Intelligent Document Classification**: Auto-classify documents as financial, market research, internal, or general
- **Smart Text Chunking**: Break documents into meaningful chunks with sentence boundary detection
- **Vector Search**: Store and search document embeddings using Pinecone
- **Strategic AI Analysis**: Get business insights using OpenAI GPT-4
- **Professional UI**: Clean Streamlit interface designed for executives
- **Query History**: Track and review previous strategic analyses
- **Source Citations**: All insights are backed by specific document references

## 🏗️ Architecture

```
strategic_engine/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   └── requirements.txt
├── frontend/               # Streamlit frontend
│   ├── streamlit_app.py   # Main UI
│   └── requirements.txt
├── uploads/               # Document storage
├── .env                   # Environment variables
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Pinecone API Key and Environment

### 1. Clone and Setup

```bash
cd strategic_engine
```

### 2. Environment Configuration

Update the `.env` file with your API keys:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_actual_openai_api_key

# Pinecone Configuration
PINECONE_API_KEY=your_actual_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=strategic-docs

# Database Configuration
DATABASE_URL=sqlite:///./strategic_engine.db
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd ../frontend
pip install -r requirements.txt
```

### 5. Start the Backend Server

```bash
cd ../backend
python -m app.main
```

The API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### 6. Start the Frontend (New Terminal)

```bash
cd frontend
streamlit run streamlit_app.py
```

The web interface will be available at: http://localhost:8501

## 📖 Usage Guide

### 1. Upload Documents

1. Use the sidebar to upload PDF, DOCX, or TXT files
2. Select document type or use "auto" for automatic classification
3. Wait for processing and embedding generation

### 2. Ask Strategic Questions

1. Use sample questions or write your own
2. Optionally filter by document type
3. Click "Analyze" to get AI-powered insights

### 3. Review Results

- Get comprehensive strategic analysis
- See confidence scores and source citations
- Review which documents were used
- Check query history for previous analyses

## 🎯 Sample Strategic Questions

- "Create a SWOT analysis using our internal reports and market data"
- "Should we expand to the European market based on our current financial position?"
- "What are our main revenue drivers according to the latest financial reports?"
- "Analyze our competitive position in the market"
- "What operational improvements can increase our profitability?"
- "Identify potential risks and mitigation strategies from our documents"

## 🔧 API Endpoints

### Document Management
- `POST /api/upload-document` - Upload and process documents
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{id}` - Delete document

### Query Processing
- `POST /api/query` - Submit strategic questions
- `GET /api/query-history` - Get query history

### System
- `GET /health` - Health check
- `GET /api/stats` - System statistics

## 🗄️ Database Schema

### Documents Table
- `id`: Primary key
- `filename`: Original filename
- `content`: Extracted text
- `document_type`: Classification (financial, market_research, internal, general)
- `upload_date`: Upload timestamp
- `metadata`: Additional metadata (JSON)
- `embedding_status`: Processing status

### Query History Table
- `id`: Primary key
- `query`: User question
- `response`: AI-generated response
- `sources`: Source documents (JSON)
- `timestamp`: Query timestamp
- `confidence_score`: Average similarity score

## 🔍 Technical Details

### Document Processing
- **Text Extraction**: PyPDF2 for PDFs, python-docx for Word documents
- **Chunking**: 1000 characters with 200 character overlap
- **Classification**: Keyword-based auto-classification
- **Embeddings**: OpenAI text-embedding-ada-002

### RAG Pipeline
1. **Query Processing**: Convert question to embedding
2. **Vector Search**: Find similar chunks in Pinecone
3. **Context Preparation**: Combine relevant chunks
4. **Response Generation**: GPT-4 with strategic business prompts
5. **Source Tracking**: Maintain document citations

## 🛠️ Development

### Running Tests

```bash
# Test document processor
cd backend/app/services
python document_processor.py

# Test OpenAI service
python openai_service.py

# Test RAG service
python rag_service.py
```

### Project Structure Details

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py      # SQLAlchemy models
│   └── services/
│       ├── __init__.py
│       ├── document_processor.py  # Document processing
│       ├── openai_service.py      # OpenAI integration
│       └── rag_service.py         # RAG implementation
└── requirements.txt
```

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure backend server is running on port 8000
   - Check if all dependencies are installed

2. **OpenAI API Error**
   - Verify your OpenAI API key in `.env`
   - Check API quota and billing

3. **Pinecone Connection Error**
   - Verify Pinecone API key and environment
   - Ensure index name is correct

4. **Document Upload Fails**
   - Check file format (PDF, DOCX, TXT only)
   - Ensure file is not corrupted
   - Check file size limits

### Logs and Debugging

- Backend logs appear in the terminal running the FastAPI server
- Set `DEBUG=True` in `.env` for detailed error messages
- Check Streamlit logs in the frontend terminal

## 📊 Performance Notes

- **Document Processing**: ~30 seconds for typical business documents
- **Query Response**: ~5-10 seconds depending on document corpus size
- **Concurrent Users**: Supports 5+ concurrent users
- **Document Limit**: No hard limit, but performance may degrade with 100+ documents

## 🔒 Security Notes

⚠️ **This is a testing/development version**:
- API keys are stored in plain text
- No user authentication
- CORS is open to all origins
- No input sanitization beyond basic validation

For production use, implement proper security measures.

## 📝 License

This project is for educational and testing purposes.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at http://localhost:8000/docs
3. Check logs for detailed error messages

---

**Strategic Decision Engine v1.0** - Empowering executives with AI-driven insights 🎯