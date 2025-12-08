"""
Offline Multimodal RAG - Performance Profiled Version

Added timing logs throughout the pipeline to identify bottlenecks
"""

import os
import json
import uuid
import time
from pathlib import Path
from typing import List, Dict, Any, TypedDict, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Document processing
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

# Embeddings
from sentence_transformers import SentenceTransformer

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# BM25
from rank_bm25 import BM25Okapi

# HTTP client
import requests

# -----------------------------------------------------------------------------
# Performance Timer Utility
# -----------------------------------------------------------------------------
class Timer:
    """Simple context manager for timing code blocks"""
    def __init__(self, name: str):
        self.name = name
        self.start = None
        
    def __enter__(self):
        self.start = time.time()
        print(f"⏱️  [{self.name}] Starting...")
        return self
        
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        print(f"⏱️  [{self.name}] Completed in {elapsed:.3f}s")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
class Config:
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "multimodal_docs")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    SLM_MODEL = os.getenv("SLM_MODEL", "phi3:latest")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
    VLM_MODEL = os.getenv("VLM_MODEL", "qwen2.5vl:latest")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
    TOP_K = int(os.getenv("TOP_K", "5"))
    DENSE_LIMIT = int(os.getenv("DENSE_LIMIT", "10"))
    SPARSE_LIMIT = int(os.getenv("SPARSE_LIMIT", "10"))

# -----------------------------------------------------------------------------
# Pydantic models
# -----------------------------------------------------------------------------
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
    citations: List[Dict[str, Any]]

# -----------------------------------------------------------------------------
# App init
# -----------------------------------------------------------------------------
app = FastAPI(title="Offline Multimodal RAG (Profiled)", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------------------------------------------------------------
# Clients & Models
# -----------------------------------------------------------------------------
qdrant_client = QdrantClient(url=Config.QDRANT_URL)

# Load embedding model
with Timer("Load Embedding Model"):
    try:
        embedder = SentenceTransformer(Config.EMBED_MODEL)
        print(f"✅ Loaded embedding model: {Config.EMBED_MODEL}")
    except Exception as e:
        print(f"⚠️ Failed to load {Config.EMBED_MODEL}, using fallback: {e}")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> List[float]:
    """Embed text with timing"""
    start = time.time()
    vec = embedder.encode(text, show_progress_bar=False)
    elapsed = time.time() - start
    print(f"    ⏱️  Embedding ({len(text)} chars) took {elapsed:.3f}s")
    return vec.tolist()

# In-memory BM25 structures
bm25_texts: List[str] = []
bm25_point_ids: List[str] = []
bm25_index: BM25Okapi = None
point_metadata: Dict[str, Dict[str, Any]] = {}

# Model cache
available_models_cache: Optional[List[str]] = None

# -----------------------------------------------------------------------------
# Collection management - SINGLE vector (text only, images stored as base64)
# -----------------------------------------------------------------------------
def ensure_collection():
    with Timer("Check/Create Qdrant Collection"):
        try:
            collection_info = qdrant_client.get_collection(collection_name=Config.COLLECTION_NAME)
            print(f"✅ Collection '{Config.COLLECTION_NAME}' exists with {collection_info.points_count} points")
        except Exception:
            print(f"📦 Creating collection '{Config.COLLECTION_NAME}'...")
            vector_size = len(embed_text("test"))
            qdrant_client.create_collection(
                collection_name=Config.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                ),
            )
            print(f"✅ Collection created with vector size: {vector_size}")

ensure_collection()

# -----------------------------------------------------------------------------
# Ollama utilities
# -----------------------------------------------------------------------------
def get_available_models() -> List[str]:
    """Get available Ollama models"""
    global available_models_cache
    
    if available_models_cache:
        return available_models_cache
    
    try:
        with Timer("Fetch Ollama Models"):
            r = requests.get(f"{Config.OLLAMA_URL.rstrip('/')}/api/tags", timeout=5)
            if r.status_code == 200:
                data = r.json()
                available_models_cache = [m.get("name", "") for m in data.get("models", [])]
                print(f"    Available models: {available_models_cache}")
                return available_models_cache
    except Exception as e:
        print(f"⚠️ Failed to get models: {e}")
    
    return []

def normalize_model_name(model: str) -> str:
    """Normalize model name to match available models"""
    available = get_available_models()
    
    if model in available:
        return model
    
    for avail in available:
        if model in avail or avail in model:
            print(f"📝 Model normalized: '{model}' -> '{avail}'")
            return avail
        
        model_base = model.replace("-", "").replace("_", "").split(":")[0].lower()
        avail_base = avail.replace("-", "").replace("_", "").split(":")[0].lower()
        if model_base == avail_base:
            print(f"📝 Model normalized: '{model}' -> '{avail}'")
            return avail
    
    print(f"⚠️ Model '{model}' not found in: {available}")
    return model

def call_ollama(
    model: str,
    prompt: str,
    images: List[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> str:
    """Call Ollama with detailed timing"""
    
    model = normalize_model_name(model)
    url = f"{Config.OLLAMA_URL.rstrip('/')}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        }
    }
    
    if images and any(x in model.lower() for x in ["vl", "vision", "llava", "bakllava"]):
        clean_images = []
        for img in images:
            if img.startswith("data:"):
                img = img.split(",", 1)[1] if "," in img else img
            clean_images.append(img)
        payload["images"] = clean_images
        print(f"    📷 Including {len(clean_images)} images")
    
    try:
        print(f"🤖 Calling {model} (prompt: {len(prompt)} chars, max_tokens: {max_tokens})")
        start = time.time()
        
        r = requests.post(url, json=payload, timeout=180)
        
        elapsed = time.time() - start
        
        if r.status_code != 200:
            error_msg = r.text[:200]
            print(f"❌ Ollama error {r.status_code} after {elapsed:.3f}s: {error_msg}")
            return f"[LLM_ERROR] {r.status_code}: {error_msg}"
        
        data = r.json()
        
        if "response" in data:
            result = data["response"].strip()
            print(f"✅ LLM response received in {elapsed:.3f}s ({len(result)} chars)")
            return result
        
        print(f"⚠️ Unexpected response format after {elapsed:.3f}s")
        return json.dumps(data)
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout after 180s")
        return "[LLM_ERROR] Request timed out"
    except Exception as e:
        print(f"❌ Error: {e}")
        return f"[LLM_ERROR] {str(e)}"

# -----------------------------------------------------------------------------
# Document processing
# -----------------------------------------------------------------------------
def process_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Process PDF with timing"""
    print(f"📄 Processing PDF: {file_path}")
    
    with Timer("PDF Partition"):
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True
        )
    
    with Timer("PDF Chunking"):
        chunks = chunk_by_title(
            elements,
            max_characters=3000,
            new_after_n_chars=2400,
            combine_text_under_n_chars=500
        )
    
    processed = []
    for chunk in chunks:
        chunk_data = {
            "chunk_id": str(uuid.uuid4()),
            "text": chunk.text or "",
            "tables": [],
            "images": [],
            "metadata": {
                "page": getattr(getattr(chunk, 'metadata', None), 'page_number', 0),
                "type": "mixed"
            }
        }
        
        if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
            for el in chunk.metadata.orig_elements:
                et = type(el).__name__
                if et == "Table":
                    table_html = getattr(getattr(el, "metadata", None), "text_as_html", getattr(el, "text", None))
                    if table_html:
                        chunk_data["tables"].append(table_html)
                        chunk_data["metadata"]["type"] = "table"
                elif et == "Image":
                    img_b64 = getattr(getattr(el, "metadata", None), "image_base64", None)
                    if img_b64:
                        chunk_data["images"].append(img_b64)
                        chunk_data["metadata"]["type"] = "image"
        
        processed.append(chunk_data)
    
    print(f"✅ Extracted {len(processed)} chunks")
    return processed

# -----------------------------------------------------------------------------
# Summarizer
# -----------------------------------------------------------------------------
def create_multimodal_summary(chunk: Dict[str, Any]) -> str:
    """Create summary with timing"""
    short_text = (chunk.get("text") or "")[:1200]
    
    prompt = f"""Summarize this text in 2-3 sentences. Be concise.

Text:
{short_text}

Summary:"""
    
    with Timer(f"SLM Summary (chunk {chunk.get('chunk_id', '')[:8]})"):
        out = call_ollama(Config.SLM_MODEL, prompt, images=None, max_tokens=200, temperature=0.3)
    
    if out.startswith("[LLM_ERROR]"):
        return short_text[:400]
    
    return out.strip() or short_text[:400]

# -----------------------------------------------------------------------------
# Store in Qdrant + BM25
# -----------------------------------------------------------------------------
def store_in_vectordb(chunks: List[Dict[str, Any]], document_id: str, filename: str):
    """Store with detailed timing"""
    global bm25_texts, bm25_point_ids, bm25_index, point_metadata
    
    print(f"💾 Storing {len(chunks)} chunks...")
    
    with Timer("Generate Summaries"):
        summaries = []
        for i, chunk in enumerate(chunks):
            print(f"  Processing chunk {i+1}/{len(chunks)}")
            summary = create_multimodal_summary(chunk)
            summaries.append(summary)
    
    with Timer("Generate Embeddings"):
        points = []
        for i, (chunk, summary) in enumerate(zip(chunks, summaries)):
            searchable_text = summary
            if chunk.get("text"):
                searchable_text = (searchable_text + "\n\n" + chunk.get("text")).strip()
            
            print(f"  Embedding chunk {i+1}/{len(chunks)}")
            vec = embed_text(searchable_text[:2000])  # Limit text length
            pid = str(uuid.uuid4())
            
            payload = {
                "document_id": document_id,
                "chunk_id": chunk["chunk_id"],
                "filename": filename,
                "text": chunk.get("text", ""),
                "tables": json.dumps(chunk.get("tables", [])),
                "images": json.dumps(chunk.get("images", [])),
                "page": chunk.get("metadata", {}).get("page", 0),
                "content_type": chunk.get("metadata", {}).get("type", "mixed"),
                "searchable_text": searchable_text
            }
            
            # FIXED: Use 'vector' not 'vectors' for single vector
            points.append(PointStruct(id=pid, vector=vec, payload=payload))
            bm25_point_ids.append(pid)
            bm25_texts.append(searchable_text)
            point_metadata[pid] = payload
    
    with Timer("Upsert to Qdrant"):
        if points:
            qdrant_client.upsert(
                collection_name=Config.COLLECTION_NAME,
                points=points
            )
            print(f"✅ Upserted {len(points)} points")
    
    with Timer("Rebuild BM25 Index"):
        if bm25_texts:
            tokenized = [doc.split() for doc in bm25_texts]
            bm25_index = BM25Okapi(tokenized)
            print(f"✅ BM25 index updated ({len(bm25_texts)} docs)")

# -----------------------------------------------------------------------------
# Hybrid retrieval
# -----------------------------------------------------------------------------
def rrf_fusion(dense_hits: List[Any], sparse_ids: List[str], top_k: int) -> List[Dict[str, Any]]:
    """RRF fusion with timing"""
    score_map = {}
    k = 60
    
    for rank, hit in enumerate(dense_hits, start=1):
        pid = hit.id
        score_map.setdefault(pid, 0.0)
        score_map[pid] += 1.0 / (k + rank)
    
    for rank, pid in enumerate(sparse_ids, start=1):
        score_map.setdefault(pid, 0.0)
        score_map[pid] += 1.0 / (k + rank)
    
    merged = sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    out = []
    for pid, sc in merged:
        meta = point_metadata.get(pid, {})
        out.append({"point_id": pid, "score": sc, "payload": meta})
    
    return out

def hybrid_search(query: str, top_k: int = Config.TOP_K) -> List[Dict[str, Any]]:
    """Hybrid search with detailed timing"""
    print(f"🔍 Searching for: '{query}'")
    
    with Timer("Query Embedding"):
        qvec = embed_text(query)
    
    with Timer("Dense Search (Qdrant)"):
        dense_hits = qdrant_client.query_points(
            collection_name=Config.COLLECTION_NAME,
            query=qvec,
            limit=Config.DENSE_LIMIT,
            with_payload=True
        ).points
        print(f"    Found {len(dense_hits)} dense results")
    
    with Timer("Sparse Search (BM25)"):
        sparse_ids = []
        if bm25_index is not None and bm25_texts:
            tokenized_query = query.split()
            top_docs = bm25_index.get_top_n(tokenized_query, bm25_texts, n=Config.SPARSE_LIMIT)
            for doc in top_docs:
                try:
                    idx = bm25_texts.index(doc)
                    sparse_ids.append(bm25_point_ids[idx])
                except ValueError:
                    continue
            print(f"    Found {len(sparse_ids)} sparse results")
    
    with Timer("RRF Fusion"):
        merged = rrf_fusion(dense_hits, sparse_ids, top_k)
        print(f"    Merged to {len(merged)} results")
    
    context = []
    for m in merged:
        p = m["payload"]
        context.append({
            "chunk_id": p.get("chunk_id"),
            "text": p.get("text"),
            "tables": json.loads(p.get("tables", "[]")),
            "images": json.loads(p.get("images", "[]")),
            "source": p.get("filename"),
            "page": p.get("page"),
            "score": m["score"],
            "searchable_text": p.get("searchable_text", "")
        })
    
    return context

# -----------------------------------------------------------------------------
# Answer generation
# -----------------------------------------------------------------------------
def generate_cited_answer(query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate answer with timing"""
    print(f"🤖 Generating answer with {len(context)} context chunks")
    
    with Timer("Build Context"):
        context_text = ""
        for idx, chunk in enumerate(context):
            context_text += f"\n[{idx+1}] Source: {chunk.get('source')} (Page {chunk.get('page')})\n"
            context_text += f"{chunk.get('text')[:500]}\n"  # Limit context size
    
    prompt = f"""Answer the question using ONLY the provided sources. Include citations like [1], [2].

QUESTION: {query}

SOURCES:
{context_text}

ANSWER (with citations):"""
    
    images = []
    for chunk in context[:2]:  # Max 2 chunks with images
        for img_b64 in (chunk.get("images") or [])[:1]:  # Max 1 image per chunk
            images.append(f"data:image/jpeg;base64,{img_b64}")
    
    model_to_use = Config.VLM_MODEL if images else Config.LLM_MODEL
    
    with Timer(f"LLM Generation ({model_to_use})"):
        answer_text = call_ollama(model_to_use, prompt, images=images, max_tokens=512, temperature=0.7)
    
    with Timer("Extract Citations"):
        citations = []
        for idx, chunk in enumerate(context):
            tag = f"[{idx+1}]"
            if tag in answer_text:
                citations.append(Citation(
                    text=(chunk.get("text") or "")[:200] + "...",
                    source=chunk.get("source"),
                    page=int(chunk.get("page") or 0),
                    chunk_id=chunk.get("chunk_id"),
                    confidence=float(chunk.get("score") or 0.0)
                ))
        print(f"    Extracted {len(citations)} citations")
    
    return {"answer": answer_text, "citations": citations}

# -----------------------------------------------------------------------------
# Workflow nodes
# -----------------------------------------------------------------------------
def retrieval_node(state: RAGState) -> RAGState:
    state["context"] = hybrid_search(state["query"], top_k=Config.TOP_K)
    return state

def generation_node(state: RAGState) -> RAGState:
    res = generate_cited_answer(state["query"], state["context"])
    state["answer"] = res["answer"]
    state["citations"] = res["citations"]
    return state

# -----------------------------------------------------------------------------
# Image processing (SIMPLIFIED - no VLM, just Tesseract OCR)
# -----------------------------------------------------------------------------
def process_image(file_path: str, filename: str) -> List[Dict[str, Any]]:
    """Process image file with OCR only (no vision model)"""
    print(f"🖼️  Processing Image: {file_path}")
    
    import base64
    from PIL import Image as PILImage
    
    with Timer("Load and Encode Image"):
        # Read and encode image
        with open(file_path, "rb") as f:
            img_data = f.read()
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        # Get image dimensions
        try:
            img = PILImage.open(file_path)
            width, height = img.size
            print(f"    Image size: {width}x{height}")
        except Exception as e:
            print(f"    Could not read image dimensions: {e}")
            width, height = 0, 0
    
    # Create a single chunk for the image
    chunk_data = {
        "chunk_id": str(uuid.uuid4()),
        "text": "",  # Will be filled by OCR or description
        "tables": [],
        "images": [img_b64],
        "metadata": {
            "page": 1,
            "type": "image",
            "width": width,
            "height": height
        }
    }
    
    # Try Tesseract OCR first (fast)
    with Timer("Tesseract OCR"):
        try:
            import pytesseract
            img_pil = PILImage.open(file_path)
            ocr_text = pytesseract.image_to_string(img_pil)
            if ocr_text.strip():
                chunk_data["text"] = f"Image OCR text:\n{ocr_text.strip()}"
                print(f"    Extracted {len(ocr_text.split())} words via OCR")
            else:
                print(f"    No text found via OCR")
        except Exception as e:
            print(f"    ⚠️  OCR failed: {e}")
    
    # If no OCR text, add basic description
    if not chunk_data["text"]:
        chunk_data["text"] = f"Image file: {filename} ({width}x{height})"
        print(f"    Using filename as description")
    
    print(f"✅ Created 1 chunk for image")
    return [chunk_data]

# -----------------------------------------------------------------------------
# API endpoints
# -----------------------------------------------------------------------------
@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document (PDF or Image)"""
    
    print("\n" + "="*80)
    print(f"📤 NEW UPLOAD: {file.filename}")
    print("="*80)
    
    # Check file type
    file_ext = file.filename.lower().split('.')[-1]
    supported_images = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    
    if file_ext not in ['pdf'] + supported_images:
        raise HTTPException(400, f"Unsupported file type. Supported: PDF, {', '.join(supported_images)}")
    
    document_id = str(uuid.uuid4())
    file_path = Config.UPLOAD_DIR / f"{document_id}_{file.filename}"
    
    with Timer(f"Save Upload ({file.filename})"):
        with open(file_path, "wb") as f:
            f.write(await file.read())
    
    try:
        with Timer(f"Process Document ({file.filename})"):
            # Process based on file type
            if file_ext == 'pdf':
                chunks = process_pdf(str(file_path))
            else:
                chunks = process_image(str(file_path), file.filename)
            
            store_in_vectordb(chunks, document_id, file.filename)
        
        print(f"\n✅ Upload completed")
        print("="*80 + "\n")
        
        return UploadResponse(
            message=f"{'PDF' if file_ext == 'pdf' else 'Image'} processed successfully",
            document_id=document_id,
            filename=file.filename,
            chunks_processed=len(chunks)
        )
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(req: QueryRequest):
    """Query documents"""
    print("\n" + "="*80)
    print(f"📥 NEW QUERY: {req.query}")
    print("="*80)
    
    start = datetime.now()
    
    try:
        with Timer("TOTAL QUERY TIME"):
            state: RAGState = {
                "query": req.query,
                "context": [],
                "answer": "",
                "citations": []
            }
            
            with Timer("Retrieval Phase"):
                state = retrieval_node(state)
            
            with Timer("Generation Phase"):
                state = generation_node(state)
        
        elapsed = (datetime.now() - start).total_seconds()
        
        print(f"\n✅ Query completed in {elapsed:.3f}s")
        print("="*80 + "\n")
        
        return QueryResponse(
            query=req.query,
            answer=state["answer"],
            citations=state["citations"],
            processing_time=elapsed
        )
    except Exception as e:
        print(f"❌ Query error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0-profiled",
        "models": {
            "slm": Config.SLM_MODEL,
            "llm": Config.LLM_MODEL,
            "vlm": Config.VLM_MODEL,
            "embedder": Config.EMBED_MODEL
        }
    }

@app.get("/debug/ollama")
async def debug_ollama():
    """Debug Ollama"""
    try:
        with Timer("Ollama Debug Check"):
            models = get_available_models()
            test = call_ollama(Config.SLM_MODEL, "Say hello", max_tokens=10)
        
        return {
            "status": "healthy",
            "ollama_url": Config.OLLAMA_URL,
            "available_models": models,
            "test_generation": test[:100]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/qdrant")
async def debug_qdrant():
    """Debug Qdrant"""
    try:
        collection_info = qdrant_client.get_collection(collection_name=Config.COLLECTION_NAME)
        return {
            "status": "healthy",
            "points_count": collection_info.points_count,
            "bm25_docs": len(bm25_texts)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*80)
    print("🚀 Offline Multimodal RAG System (PROFILED VERSION)")
    print("="*80)
    print(f"📍 Qdrant: {Config.QDRANT_URL}")
    print(f"🤖 Ollama: {Config.OLLAMA_URL}")
    print(f"📦 Collection: {Config.COLLECTION_NAME}")
    print(f"🧠 SLM: {Config.SLM_MODEL}")
    print(f"🧠 LLM: {Config.LLM_MODEL}")
    print(f"🧠 VLM: {Config.VLM_MODEL}")
    print(f"🔢 Embedder: {Config.EMBED_MODEL}")
    print("="*80 + "\n")

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)