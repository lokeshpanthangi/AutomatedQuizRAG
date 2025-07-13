import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Strategic Decision Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border-left: 5px solid #1f4e79;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .source-citation {
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #28a745;
        margin: 0.25rem 0;
        font-size: 0.9rem;
    }
    
    .confidence-score {
        background: #e8f5e8;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    
    .sample-question {
        background: #f0f8ff;
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 3px solid #007bff;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .sample-question:hover {
        background: #e6f3ff;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def make_api_request(endpoint, method="GET", data=None, files=None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, data=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to API. Please ensure the backend server is running on http://localhost:8000"
    except Exception as e:
        return None, f"Error: {str(e)}"

def check_api_health():
    """Check if API is healthy"""
    result, error = make_api_request("/health")
    if result:
        return result.get("status") == "healthy"
    return False

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Main header
st.markdown('<div class="main-header">🎯 Strategic Decision Engine</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.1rem;'>AI-Powered Strategic Planning Platform for Executives</p>", unsafe_allow_html=True)

# Check API health
api_healthy = check_api_health()
if not api_healthy:
    st.error("⚠️ Backend API is not responding. Please start the backend server first.")
    st.info("To start the backend: Navigate to the backend directory and run: `python -m app.main`")
    st.stop()

# Sidebar for document management
with st.sidebar:
    st.header("📁 Document Management")
    
    # Document upload section
    st.subheader("Upload Document")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt'],
        help="Upload PDF, DOCX, or TXT files for analysis"
    )
    
    document_type = st.selectbox(
        "Document Type",
        ["auto", "financial", "market_research", "internal", "general"],
        help="Select document type or use 'auto' for automatic classification"
    )
    
    if st.button("📤 Upload Document", type="primary"):
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"document_type": document_type}
                
                result, error = make_api_request("/api/upload-document", "POST", data=data, files=files)
                
                if result:
                    st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully!")
                    st.info(f"📊 Created {result['chunks_created']} chunks for analysis")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Upload failed: {error}")
        else:
            st.warning("Please select a file to upload.")
    
    st.divider()
    
    # Document list section
    st.subheader("📚 Uploaded Documents")
    
    # Refresh documents
    if st.button("🔄 Refresh List"):
        st.rerun()
    
    # Get documents from API
    docs_result, docs_error = make_api_request("/api/documents")
    
    if docs_result:
        documents = docs_result.get("documents", [])
        
        if documents:
            for doc in documents:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{doc['filename']}**")
                        st.caption(f"Type: {doc['document_type']} | Words: {doc['word_count']}")
                        
                        # Status indicator
                        status = doc['embedding_status']
                        if status == 'completed':
                            st.success("✅ Ready", icon="✅")
                        elif status == 'pending':
                            st.warning("⏳ Processing", icon="⏳")
                        else:
                            st.error("❌ Failed", icon="❌")
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc['id']}", help="Delete document"):
                            with st.spinner("Deleting..."):
                                result, error = make_api_request(f"/api/documents/{doc['id']}", "DELETE")
                                if result:
                                    st.success("Document deleted!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Delete failed: {error}")
                
                st.divider()
        else:
            st.info("No documents uploaded yet.")
    else:
        st.error(f"Failed to load documents: {docs_error}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🤔 Strategic Analysis")
    
    # Sample questions
    st.subheader("💡 Sample Strategic Questions")
    
    sample_questions = [
        "Create a SWOT analysis using our internal reports and market data",
        "Should we expand to the European market based on our current financial position?",
        "What are our main revenue drivers according to the latest financial reports?",
        "Analyze our competitive position in the market",
        "What operational improvements can increase our profitability?",
        "Identify potential risks and mitigation strategies from our documents"
    ]
    
    selected_question = None
    for i, question in enumerate(sample_questions):
        if st.button(f"💭 {question}", key=f"sample_{i}", help="Click to use this question"):
            selected_question = question
    
    st.divider()
    
    # Query input
    st.subheader("📝 Your Strategic Question")
    
    # Document type filter
    doc_filter = st.selectbox(
        "Filter by Document Type (Optional)",
        ["all", "financial", "market_research", "internal", "general"],
        help="Filter analysis to specific document types"
    )
    
    # Text input for query
    query_text = st.text_area(
        "Enter your strategic question:",
        value=selected_question if selected_question else "",
        height=100,
        placeholder="e.g., What are the key growth opportunities based on our market research?"
    )
    
    # Analyze button
    if st.button("🔍 Analyze", type="primary", disabled=not query_text.strip()):
        if query_text.strip():
            with st.spinner("🧠 Analyzing your question using AI..."):
                data = {
                    "query": query_text,
                    "document_type_filter": doc_filter
                }
                
                result, error = make_api_request("/api/query", "POST", data=data)
                
                if result:
                    st.success("✅ Analysis completed!")
                    
                    # Display response
                    st.subheader("📊 Strategic Analysis Results")
                    
                    # Main response
                    st.markdown("### 🎯 Strategic Insights")
                    st.markdown(result['response'])
                    
                    # Confidence and metadata
                    col_conf1, col_conf2, col_conf3 = st.columns(3)
                    
                    with col_conf1:
                        st.markdown(
                            f'<div class="confidence-score">Confidence Score<br><strong>{result["confidence_score"]}</strong></div>',
                            unsafe_allow_html=True
                        )
                    
                    with col_conf2:
                        st.markdown(
                            f'<div class="confidence-score">Sources Found<br><strong>{len(result["sources"])}</strong></div>',
                            unsafe_allow_html=True
                        )
                    
                    with col_conf3:
                        st.markdown(
                            f'<div class="confidence-score">Chunks Analyzed<br><strong>{result["chunks_found"]}</strong></div>',
                            unsafe_allow_html=True
                        )
                    
                    # Source citations
                    if result['sources']:
                        st.markdown("### 📚 Source Documents")
                        for i, source in enumerate(result['sources'], 1):
                            st.markdown(
                                f'<div class="source-citation">📄 {i}. {source}</div>',
                                unsafe_allow_html=True
                            )
                    
                    # Save to session state for history
                    st.session_state.query_history.insert(0, {
                        'query': query_text,
                        'response': result['response'][:200] + "...",
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'sources': result['sources']
                    })
                    
                else:
                    st.error(f"Analysis failed: {error}")
        else:
            st.warning("Please enter a question to analyze.")

with col2:
    st.header("📈 System Status")
    
    # Get system stats
    stats_result, stats_error = make_api_request("/api/stats")
    
    if stats_result:
        st.markdown(
            f'<div class="metric-card">📄 <strong>Total Documents:</strong> {stats_result.get("total_documents", 0)}</div>',
            unsafe_allow_html=True
        )
        
        st.markdown(
            f'<div class="metric-card">❓ <strong>Total Queries:</strong> {stats_result.get("total_queries", 0)}</div>',
            unsafe_allow_html=True
        )
        
        # Document type distribution
        doc_types = stats_result.get("document_types", {})
        if doc_types:
            st.subheader("📊 Document Types")
            for doc_type, count in doc_types.items():
                st.markdown(
                    f'<div class="metric-card">{doc_type.title()}: <strong>{count}</strong></div>',
                    unsafe_allow_html=True
                )
    
    st.divider()
    
    # Recent query history
    st.subheader("🕒 Recent Queries")
    
    # Get query history from API
    history_result, history_error = make_api_request("/api/query-history?limit=5")
    
    if history_result:
        history = history_result.get("history", [])
        
        if history:
            for query in history:
                with st.expander(f"📝 {query['query'][:50]}..."):
                    st.write(f"**Query:** {query['query']}")
                    st.write(f"**Response:** {query['response']}")
                    st.write(f"**Sources:** {', '.join(query['sources'])}")
                    st.caption(f"Asked: {query['timestamp']}")
        else:
            st.info("No queries yet.")
    else:
        st.error(f"Failed to load history: {history_error}")

# Footer
st.divider()
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.9rem;'>Strategic Decision Engine v1.0 | Powered by OpenAI GPT-4 & Pinecone</p>",
    unsafe_allow_html=True
)