"""
Enhanced Multimodal RAG System with Citations
Implements: PDF processing, image/table handling, hybrid search, and cited answers
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import base64

# Core libraries
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime

# Document processing
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

# Vector store and embeddings
from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient, models

# LLMs
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    UPLOAD_DIR = Path("uploads")
    VECTOR_DB_URL = os.getenv("QDRANT_URL")
    VECTOR_DB_KEY = os.getenv("QDRANT_API_KEY")
    COLLECTION_NAME = "multimodal_docs"
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Models
    DENSE_MODEL = "jinaai/jina-embeddings-v2-small-en"
    SPARSE_MODEL = "Qdrant/BM25"
    LLM_MODEL = "gemini-2.0-flash-exp"
    
    # Search parameters
    TOP_K = 5
    DENSE_LIMIT = 10
    SPARSE_LIMIT = 10

# Create directories
Config.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    chunks_processed: int

class QueryRequest(BaseModel):
    query: str
    top_k: int = Config.TOP_K

class Citation(BaseModel):
    text: str
    source: str
    page: int
    chunk_id: str
    confidence: float

class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    processing_time: float

class RAGState(TypedDict):
    query: str
    context: List[Dict[str, Any]]
    answer: str
    citations: List[Citation]

# =============================================================================
# INITIALIZE COMPONENTS
# =============================================================================

# FastAPI app
app = FastAPI(title="Multimodal RAG with Citations", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embeddings
dense_model = TextEmbedding(model_name=Config.DENSE_MODEL)
sparse_model = SparseTextEmbedding(model_name=Config.SPARSE_MODEL)

# Vector store
vector_client = QdrantClient(
    url=Config.VECTOR_DB_URL,
    api_key=Config.VECTOR_DB_KEY,
)

# LLM
llm = ChatGoogleGenerativeAI(
    model=Config.LLM_MODEL,
    temperature=0,
    google_api_key=Config.GOOGLE_API_KEY
)

# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================

def process_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract elements from PDF with multimodal support"""
    
    elements = partition_pdf(
        filename=file_path,
        strategy="hi_res",
        infer_table_structure=True,
        extract_image_block_types=["Image"],
        extract_image_block_to_payload=True
    )
    
    # Create chunks
    chunks = chunk_by_title(
        elements,
        max_characters=3000,
        new_after_n_chars=2400,
        combine_text_under_n_chars=500
    )
    
    processed_chunks = []
    
    for idx, chunk in enumerate(chunks):
        chunk_data = {
            'chunk_id': f"chunk_{idx}",
            'text': chunk.text,
            'tables': [],
            'images': [],
            'metadata': {
                'page': getattr(chunk.metadata, 'page_number', 0),
                'type': 'mixed'
            }
        }
        
        # Extract tables and images
        if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'orig_elements'):
            for element in chunk.metadata.orig_elements:
                element_type = type(element).__name__
                
                if element_type == 'Table':
                    table_html = getattr(element.metadata, 'text_as_html', element.text)
                    chunk_data['tables'].append(table_html)
                    chunk_data['metadata']['type'] = 'table'
                
                elif element_type == 'Image':
                    if hasattr(element.metadata, 'image_base64'):
                        chunk_data['images'].append(element.metadata.image_base64)
                        chunk_data['metadata']['type'] = 'image'
        
        processed_chunks.append(chunk_data)
    
    return processed_chunks

def create_multimodal_summary(chunk: Dict[str, Any]) -> str:
    """Create AI-enhanced searchable summary"""
    
    prompt = f"""Create a comprehensive, searchable description for this content:

TEXT: {chunk['text'][:1000]}

TABLES: {len(chunk['tables'])} table(s)
IMAGES: {len(chunk['images'])} image(s)

Generate a detailed description that:
1. Summarizes key facts, numbers, and data
2. Describes visual content (charts, diagrams)
3. Includes terms users might search for
4. Maintains factual accuracy

SEARCHABLE DESCRIPTION:"""

    try:
        message_content = [{"type": "text", "text": prompt}]
        
        # Add images to analysis
        for img_base64 in chunk['images'][:2]:  # Limit to 2 images
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
            })
        
        response = llm.invoke([HumanMessage(content=message_content)])
        return response.content
    
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return chunk['text']

def store_in_vectordb(chunks: List[Dict[str, Any]], document_id: str, filename: str):
    """Store chunks in Qdrant with hybrid vectors"""
    
    # Prepare points for insertion
    points = []
    
    for chunk in chunks:
        # Create enhanced searchable text
        searchable_text = create_multimodal_summary(chunk)
        
        # Generate embeddings
        dense_vector = next(dense_model.embed([searchable_text]))
        sparse_vector = next(sparse_model.embed([searchable_text]))
        
        point_id = str(uuid.uuid4())
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector={
                    "dense": dense_vector.tolist(),
                    "sparse": models.SparseVector(**sparse_vector.as_object())
                },
                payload={
                    "document_id": document_id,
                    "chunk_id": chunk['chunk_id'],
                    "filename": filename,
                    "text": chunk['text'],
                    "tables": json.dumps(chunk['tables']),
                    "images": json.dumps(chunk['images']),
                    "page": chunk['metadata']['page'],
                    "content_type": chunk['metadata']['type'],
                    "searchable_text": searchable_text
                }
            )
        )
    
    # Upsert to Qdrant
    vector_client.upsert(
        collection_name=Config.COLLECTION_NAME,
        points=points
    )

# =============================================================================
# RETRIEVAL & GENERATION
# =============================================================================

def hybrid_search(query: str, top_k: int = Config.TOP_K) -> List[Dict[str, Any]]:
    """Perform hybrid search with dense + sparse vectors"""
    
    # Generate query vectors
    dense_vector = next(dense_model.embed([query]))
    sparse_vector = next(sparse_model.embed([query]))
    
    # Prefetch from both indexes
    prefetch = [
        models.Prefetch(
            query=dense_vector.tolist(),
            using="dense",
            limit=Config.DENSE_LIMIT
        ),
        models.Prefetch(
            query=models.SparseVector(**sparse_vector.as_object()),
            using="sparse",
            limit=Config.SPARSE_LIMIT
        )
    ]
    
    # Hybrid search
    results = vector_client.query_points(
        collection_name=Config.COLLECTION_NAME,
        prefetch=prefetch,
        query=dense_vector.tolist(),
        using="dense",
        with_payload=True,
        limit=top_k
    )
    
    # Format results
    context = []
    for result in results.points:
        context.append({
            "chunk_id": result.payload["chunk_id"],
            "text": result.payload["text"],
            "tables": json.loads(result.payload["tables"]),
            "images": json.loads(result.payload["images"]),
            "source": result.payload["filename"],
            "page": result.payload["page"],
            "score": result.score,
            "searchable_text": result.payload.get("searchable_text", "")
        })
    
    return context

def generate_cited_answer(query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate answer with proper citations"""
    
    # Build context for LLM
    context_text = ""
    for idx, chunk in enumerate(context):
        context_text += f"\n[{idx+1}] Source: {chunk['source']} (Page {chunk['page']})\n"
        context_text += f"Text: {chunk['text']}\n"
        
        if chunk['tables']:
            context_text += f"Contains {len(chunk['tables'])} table(s)\n"
        if chunk['images']:
            context_text += f"Contains {len(chunk['images'])} image(s)\n"
    
    prompt = f"""Answer the question using ONLY the provided sources. Include citations.

QUESTION: {query}

SOURCES:
{context_text}

INSTRUCTIONS:
1. Answer accurately based on the sources
2. After EVERY fact/claim, add a citation like [1], [2], etc.
3. Use multiple citations [1,2] if info comes from multiple sources
4. If sources don't contain the answer, say "Information not found in provided sources"
5. Be specific and cite page numbers when referencing data

ANSWER WITH CITATIONS:"""

    try:
        # Add images to context for visual understanding
        message_content = [{"type": "text", "text": prompt}]
        
        # Add up to 3 images for visual context
        img_count = 0
        for chunk in context:
            for img_base64 in chunk['images']:
                if img_count < 3:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                    })
                    img_count += 1
        
        response = llm.invoke([HumanMessage(content=message_content)])
        answer = response.content
        
        # Extract citations from answer
        citations = []
        for idx, chunk in enumerate(context):
            # Check if citation [idx+1] appears in answer
            if f"[{idx+1}]" in answer:
                citations.append(Citation(
                    text=chunk['text'][:200] + "...",
                    source=chunk['source'],
                    page=chunk['page'],
                    chunk_id=chunk['chunk_id'],
                    confidence=chunk['score']
                ))
        
        return {
            "answer": answer,
            "citations": citations
        }
    
    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "citations": []
        }

# =============================================================================
# LANGGRAPH WORKFLOW
# =============================================================================

def retrieval_node(state: RAGState) -> RAGState:
    """Retrieve relevant context"""
    context = hybrid_search(state["query"])
    state["context"] = context
    return state

def generation_node(state: RAGState) -> RAGState:
    """Generate cited answer"""
    result = generate_cited_answer(state["query"], state["context"])
    state["answer"] = result["answer"]
    state["citations"] = result["citations"]
    return state

# Build workflow
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieval_node)
workflow.add_node("generate", generation_node)
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

rag_graph = workflow.compile()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process PDF document"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files supported")
    
    # Save file
    document_id = str(uuid.uuid4())
    file_path = Config.UPLOAD_DIR / f"{document_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        # Process document
        chunks = process_pdf(str(file_path))
        
        # Store in vector DB
        store_in_vectordb(chunks, document_id, file.filename)
        
        return UploadResponse(
            message="Document processed successfully",
            document_id=document_id,
            filename=file.filename,
            chunks_processed=len(chunks)
        )
    
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents with citations"""
    
    start_time = datetime.now()
    
    try:
        # Run RAG pipeline
        result = rag_graph.invoke({
            "query": request.query,
            "context": [],
            "answer": "",
            "citations": []
        })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            query=request.query,
            answer=result["answer"],
            citations=result["citations"],
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(500, f"Query failed: {str(e)}")

@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "Multimodal PDF processing",
            "Hybrid search (dense + sparse)",
            "AI-generated citations",
            "Image and table handling"
        ]
    }

# =============================================================================
# INITIALIZE VECTOR COLLECTION
# =============================================================================

def initialize_collection():
    """Create Qdrant collection with hybrid vectors"""
    
    try:
        vector_client.create_collection(
            collection_name=Config.COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=512,  # Jina embeddings size
                    distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams()
            }
        )
        print(f"✅ Collection '{Config.COLLECTION_NAME}' created")
    except Exception as e:
        print(f"Collection already exists or error: {e}")

# Initialize on startup
initialize_collection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)