# main.py
"""
FastAPI AI service (project-scoped Qdrant collections + per-project BM25)
Features:
 - Tesseract OCR for image text extraction
 - CLIP image vectors + text vectors (sentence-transformers)
 - Per-project Qdrant collections: "project_<project_id>"
 - Per-project BM25 indices (in-memory)
 - Text-only LLM generation via Ollama
 - Fallback for legacy single-vector Qdrant deployments (concatenate vectors)
"""

import os
import json
import uuid
import time
from pathlib import Path
from typing import List, Dict, Any, TypedDict, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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

# OCR + Image
import pytesseract
from PIL import Image
import base64

# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------
class Timer:
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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
class Config:
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    SLM_MODEL = os.getenv("SLM_MODEL", "phi3:latest")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
    CLIP_MODEL = os.getenv("CLIP_MODEL", "clip-ViT-B-32")
    TOP_K = int(os.getenv("TOP_K", "5"))
    DENSE_LIMIT = int(os.getenv("DENSE_LIMIT", "10"))
    SPARSE_LIMIT = int(os.getenv("SPARSE_LIMIT", "10"))
    # Minimum image vector length threshold to consider image vector valid
    MIN_IMAGE_VEC_LEN = 4

# ---------------------------------------------------------------------------
# Pydantic / types
# ---------------------------------------------------------------------------
class UploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    chunks_processed: int

class QueryRequest(BaseModel):
    project_id: str
    query: str
    chat_id: Optional[str] = None
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

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Service - Project Qdrant + BM25", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---------------------------------------------------------------------------
# Qdrant client + capabilities
# ---------------------------------------------------------------------------
qdrant_client = QdrantClient(url=Config.QDRANT_URL)

# We'll attempt to use named vectors; if the server or client doesn't support it,
# we'll fallback to legacy single-vector mode by concatenating vectors.
USE_NAMED_VECTORS = True

def detect_qdrant_named_vector_support():
    global USE_NAMED_VECTORS
    try:
        # Try to create a temporary collection using named vectors (in memory test)
        test_name = f"__temp_named_vectors_test_{uuid.uuid4().hex[:6]}"
        text_size = 4
        image_size = 4
        qdrant_client.create_collection(
            collection_name=test_name,
            vectors_config={
                "text": VectorParams(size=text_size, distance=Distance.COSINE),
                "image": VectorParams(size=image_size, distance=Distance.COSINE)
            }
        )
        qdrant_client.delete_collection(test_name)
        USE_NAMED_VECTORS = True
        print("✅ Qdrant supports named vectors.")
    except Exception as e:
        USE_NAMED_VECTORS = False
        print(f"⚠️ Qdrant named-vectors unsupported or client mismatch: {e}. Falling back to single-vector mode.")

detect_qdrant_named_vector_support()

# ---------------------------------------------------------------------------
# Embedders
# ---------------------------------------------------------------------------
with Timer("Load Text Embedding Model"):
    try:
        text_embedder = SentenceTransformer(Config.EMBED_MODEL)
        print(f"✅ Loaded text embedder: {Config.EMBED_MODEL}")
    except Exception as e:
        print(f"⚠️ Failed to load {Config.EMBED_MODEL}: {e}")
        text_embedder = SentenceTransformer("all-MiniLM-L6-v2")

with Timer("Load CLIP Image Model"):
    try:
        image_embedder = SentenceTransformer(Config.CLIP_MODEL)
        print(f"✅ Loaded image embedder: {Config.CLIP_MODEL}")
    except Exception as e:
        print(f"⚠️ Failed to load {Config.CLIP_MODEL}: {e}")
        image_embedder = text_embedder

def embed_text(text: str) -> List[float]:
    start = time.time()
    vec = text_embedder.encode(text, show_progress_bar=False)
    elapsed = time.time() - start
    print(f"    ⏱️  Embedding text ({len(text)} chars) took {elapsed:.3f}s")
    return vec.tolist()

def embed_image_pil(img: Image.Image) -> List[float]:
    start = time.time()
    vec = image_embedder.encode([img], show_progress_bar=False)
    elapsed = time.time() - start
    print(f"    ⏱️  Embedding image took {elapsed:.3f}s")
    return vec[0].tolist()

# ---------------------------------------------------------------------------
# Per-project BM25 & metadata in-memory structures
# ---------------------------------------------------------------------------
# Each project_id has:
#   - bm25_texts_by_project[project_id] = [searchable_texts...]
#   - bm25_point_ids_by_project[project_id] = [point_ids...]
#   - bm25_index_by_project[project_id] = BM25Okapi(...)
#   - metadata_by_project[project_id] = { point_id: payload }
bm25_texts_by_project: Dict[str, List[str]] = {}
bm25_point_ids_by_project: Dict[str, List[str]] = {}
bm25_index_by_project: Dict[str, BM25Okapi] = {}
point_metadata_by_project: Dict[str, Dict[str, Dict[str, Any]]] = {}

# ---------------------------------------------------------------------------
# Helper: collection name
# ---------------------------------------------------------------------------
def get_collection_name(project_id: str) -> str:
    # sanitize project_id if necessary
    return f"project_{project_id}"

# ---------------------------------------------------------------------------
# Ensure collection (dynamic)
# ---------------------------------------------------------------------------
def ensure_collection(collection_name: str):
    with Timer(f"Check/Create collection [{collection_name}]"):
        try:
            qdrant_client.get_collection(collection_name=collection_name)
            print(f"✅ Collection '{collection_name}' exists.")
            return
        except Exception:
            print(f"📦 Creating collection '{collection_name}'...")
            if USE_NAMED_VECTORS:
                # compute sizes
                text_size = len(embed_text("test"))
                image_size = len(embed_image_pil(Image.new('RGB', (32, 32))))
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "text": VectorParams(size=text_size, distance=Distance.COSINE),
                        "image": VectorParams(size=image_size, distance=Distance.COSINE)
                    }
                )
                print(f"✅ Created named-vector collection: text={text_size}, image={image_size}")
            else:
                # fallback: single-vector size = text + image
                text_size = len(embed_text("test"))
                image_size = len(embed_image_pil(Image.new('RGB', (32, 32))))
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=text_size + image_size, distance=Distance.COSINE)
                )
                print(f"✅ Created single-vector collection (size={text_size + image_size})")

# ---------------------------------------------------------------------------
# Ollama (text-only) utilities
# ---------------------------------------------------------------------------
def get_available_models() -> List[str]:
    try:
        r = requests.get(f"{Config.OLLAMA_URL.rstrip('/')}/api/tags", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception as e:
        print(f"⚠️ Failed to fetch Ollama models: {e}")
    return []

def normalize_model_name(model: str) -> str:
    available = get_available_models()
    if model in available:
        return model
    for avail in available:
        if model in avail or avail in model:
            return avail
    return model

def call_ollama(model: str, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    model = normalize_model_name(model)
    url = f"{Config.OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature}
    }
    try:
        start = time.time()
        r = requests.post(url, json=payload, timeout=180)
        elapsed = time.time() - start
        if r.status_code != 200:
            return f"[LLM_ERROR] {r.status_code}: {r.text[:200]}"
        data = r.json()
        if "response" in data:
            return data["response"].strip()
        return json.dumps(data)
    except requests.exceptions.Timeout:
        return "[LLM_ERROR] Request timed out"
    except Exception as e:
        return f"[LLM_ERROR] {str(e)}"

# ---------------------------------------------------------------------------
# Document processing (PDF)
# ---------------------------------------------------------------------------
def process_pdf(file_path: str) -> List[Dict[str, Any]]:
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
        chunks = chunk_by_title(elements, max_characters=3000, new_after_n_chars=2400, combine_text_under_n_chars=500)

    processed = []
    for chunk in chunks:
        chunk_data = {
            "chunk_id": str(uuid.uuid4()),
            "text": chunk.text or "",
            "tables": [],
            "images": [],
            "metadata": {"page": getattr(getattr(chunk, 'metadata', None), 'page_number', 0), "type": "mixed"}
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

# ---------------------------------------------------------------------------
# Image processing: OCR + CLIP
# ---------------------------------------------------------------------------
def process_image(file_path: str, filename: str) -> List[Dict[str, Any]]:
    print(f"🖼️  Processing image: {file_path}")
    with Timer("Load Image"):
        img = Image.open(file_path).convert('RGB')
        width, height = img.size
        with open(file_path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')

    chunk_data = {
        "chunk_id": str(uuid.uuid4()),
        "text": "",
        "ocr_text": "",
        "tables": [],
        "images": [img_b64],
        "metadata": {"page": 1, "type": "image", "width": width, "height": height}
    }

    with Timer("Tesseract OCR"):
        try:
            ocr_result = pytesseract.image_to_string(img)
            chunk_data["ocr_text"] = ocr_result.strip()
            if ocr_result.strip():
                chunk_data["text"] = ocr_result.strip()
                print(f"    OCR extracted {len(ocr_result.split())} words")
        except Exception as e:
            print(f"    OCR failed: {e}")

    # optional short caption if OCR empty
    if not chunk_data["text"]:
        prompt = "Summarize the visible contents of the image in 1-2 sentences."
        with Timer("Optional caption via SLM"):
            caption = call_ollama(Config.SLM_MODEL, prompt, max_tokens=150, temperature=0.2)
            if not caption.startswith("[LLM_ERROR]"):
                chunk_data["text"] = caption.strip()

    # embed image
    with Timer("Image embedding (CLIP)"):
        try:
            img_vec = embed_image_pil(img)
            chunk_data["image_vector"] = img_vec
        except Exception as e:
            print(f"    Image embedding failed: {e}")
            chunk_data["image_vector"] = []

    print(f"✅ Created 1 chunk for image (ocr_len={len(chunk_data['ocr_text'])})")
    return [chunk_data]

# ---------------------------------------------------------------------------
# Store in Qdrant + per-project BM25
# ---------------------------------------------------------------------------
def store_in_vectordb(chunks: List[Dict[str, Any]], document_id: str, filename: str, project_id: str, chat_id: Optional[str] = None):
    """
    Stores chunks in the Qdrant collection for this project.
    Also updates per-project BM25 and metadata maps.
    """
    print(f"💾 Storing {len(chunks)} chunks into project {project_id} (chat={chat_id})...")
    collection = get_collection_name(project_id)
    ensure_collection(collection)

    # prepare per-project in-memory maps
    bm25_texts = bm25_texts_by_project.setdefault(project_id, [])
    bm25_point_ids = bm25_point_ids_by_project.setdefault(project_id, [])
    metadata_map = point_metadata_by_project.setdefault(project_id, {})

    with Timer("Generate Summaries (SLM)"):
        summaries = []
        for chunk in chunks:
            short_text = (chunk.get("text") or "")[:1200]
            prompt = f"Summarize this text in 2-3 sentences.\n\nText:\n{short_text}\n\nSummary:"
            summary = call_ollama(Config.SLM_MODEL, prompt, max_tokens=200, temperature=0.3)
            if summary.startswith("[LLM_ERROR]"):
                summary = short_text[:400]
            summaries.append(summary)

    with Timer("Generate Embeddings"):
        points = []
        for i, (chunk, summary) in enumerate(zip(chunks, summaries)):
            searchable_text = summary
            if chunk.get("text"):
                searchable_text = (searchable_text + "\n\n" + chunk.get("text")).strip()

            print(f"  Embedding chunk {i+1}/{len(chunks)}")
            text_vec = embed_text(searchable_text[:2000])
            image_vec = chunk.get("image_vector") or None

            pid = str(uuid.uuid4())
            payload = {
                "document_id": document_id,
                "chunk_id": chunk["chunk_id"],
                "filename": filename,
                "text": chunk.get("text", ""),
                "ocr_text": chunk.get("ocr_text", ""),
                "tables": json.dumps(chunk.get("tables", [])),
                "images": json.dumps(chunk.get("images", [])),
                "page": chunk.get("metadata", {}).get("page", 0),
                "content_type": chunk.get("metadata", {}).get("type", "mixed"),
                "searchable_text": searchable_text,
                "chat_id": chat_id
            }

            if USE_NAMED_VECTORS:
                vectors = {"text": text_vec}
                if image_vec and len(image_vec) >= Config.MIN_IMAGE_VEC_LEN:
                    vectors["image"] = image_vec
                points.append(PointStruct(id=pid, vectors=vectors, payload=payload))
            else:
                # legacy: combine text+image vectors
                if image_vec and len(image_vec) >= Config.MIN_IMAGE_VEC_LEN:
                    combined = text_vec + image_vec
                else:
                    combined = text_vec
                points.append(PointStruct(id=pid, vector=combined, payload=payload))

            bm25_point_ids.append(pid)
            bm25_texts.append(searchable_text)
            metadata_map[pid] = payload

    with Timer("Upsert to Qdrant"):
        if points:
            # qdrant_client.upsert supports list[PointStruct]
            qdrant_client.upsert(collection_name=collection, points=points)
            print(f"✅ Upserted {len(points)} points into {collection}")

    with Timer("Rebuild BM25 Index"):
        if bm25_texts:
            tokenized = [doc.split() for doc in bm25_texts]
            bm25_index = BM25Okapi(tokenized)
            bm25_index_by_project[project_id] = bm25_index
            print(f"✅ BM25 index updated for project {project_id} ({len(bm25_texts)} docs)")

# ---------------------------------------------------------------------------
# Hybrid search (per-project)
# ---------------------------------------------------------------------------
def rrf_fusion(dense_hits: List[Any], sparse_ids: List[str], top_k: int) -> List[Dict[str, Any]]:
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
        # payload lookup per project will be done by caller
        out.append({"point_id": pid, "score": sc})
    return out

def hybrid_search(project_id: str, query: str, top_k: int = Config.TOP_K) -> List[Dict[str, Any]]:
    print(f"🔍 Project '{project_id}' searching for: '{query}'")
    collection = get_collection_name(project_id)

    with Timer("Query Embedding (text)"):
        qvec = embed_text(query)

    dense_text_hits = []
    try:
        with Timer("Dense Search (Qdrant: text)"):
            dense_text_hits = qdrant_client.query_points(
                collection_name=collection,
                query_vector=qvec,
                limit=Config.DENSE_LIMIT,
                with_payload=True,
                vector_name="text" if USE_NAMED_VECTORS else None
            ).points
            print(f"    Found {len(dense_text_hits)} text dense results")
    except Exception as e:
        print(f"    Text-vector search failed: {e}")

    dense_image_hits = []
    if USE_NAMED_VECTORS:
        try:
            with Timer("Query Embedding (image proxy via CLIP)"):
                # encode query into CLIP space (text-to-image proxy supported by sentence-transformers)
                qimg_vec = image_embedder.encode([query], show_progress_bar=False)
            with Timer("Dense Search (Qdrant: image)"):
                dense_image_hits = qdrant_client.query_points(
                    collection_name=collection,
                    query_vector=qimg_vec[0].tolist(),
                    limit=Config.DENSE_LIMIT,
                    with_payload=True,
                    vector_name="image"
                ).points
                print(f"    Found {len(dense_image_hits)} image dense results")
        except Exception as e:
            print(f"    Image-vector search skipped/failed: {e}")

    # combine dense hits
    combined_dense = []
    id_seen = set()
    for h in (dense_text_hits + dense_image_hits):
        if h.id not in id_seen:
            combined_dense.append(h)
            id_seen.add(h.id)

    # sparse BM25 search (per-project)
    sparse_ids = []
    try:
        with Timer("Sparse Search (BM25)"):
            bm25_texts = bm25_texts_by_project.get(project_id, [])
            bm25_index = bm25_index_by_project.get(project_id)
            if bm25_index and bm25_texts:
                tokenized_query = query.split()
                top_docs = bm25_index.get_top_n(tokenized_query, bm25_texts, n=Config.SPARSE_LIMIT)
                for doc in top_docs:
                    try:
                        idx = bm25_texts.index(doc)
                        sparse_ids.append(bm25_point_ids_by_project[project_id][idx])
                    except ValueError:
                        continue
                print(f"    Found {len(sparse_ids)} sparse results")
    except Exception as e:
        print(f"    BM25 search failed: {e}")

    with Timer("RRF Fusion"):
        merged = rrf_fusion(combined_dense, sparse_ids, top_k)
        print(f"    Merged to {len(merged)} results")

    # Build context payloads
    context = []
    metadata_map = point_metadata_by_project.get(project_id, {})
    for item in merged:
        pid = item["point_id"]
        meta = metadata_map.get(pid, {})
        context.append({
            "chunk_id": meta.get("chunk_id"),
            "text": meta.get("text"),
            "ocr_text": meta.get("ocr_text"),
            "tables": json.loads(meta.get("tables", "[]")),
            "images": json.loads(meta.get("images", "[]")),
            "source": meta.get("filename"),
            "page": meta.get("page"),
            "score": float(item["score"]),
            "searchable_text": meta.get("searchable_text", ""),
            "chat_id": meta.get("chat_id")
        })
    return context

# ---------------------------------------------------------------------------
# Answer generation (text-only)
# ---------------------------------------------------------------------------
def generate_cited_answer(project_id: str, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"🤖 Generating answer for project={project_id} with {len(context)} context chunks")
    with Timer("Build Context"):
        context_text = ""
        for idx, chunk in enumerate(context):
            context_text += f"\n[{idx+1}] Source: {chunk.get('source')} (Page {chunk.get('page')})\n"
            display_text = chunk.get('ocr_text') or chunk.get('text') or ""
            context_text += f"{display_text[:1000]}\n"

    prompt = f"""Answer the question using ONLY the provided sources. Include citations like [1], [2].

PROJECT: {project_id}
QUESTION: {query}

SOURCES:
{context_text}

ANSWER (with citations):"""

    with Timer("LLM Generation (text-only)"):
        answer_text = call_ollama(Config.LLM_MODEL, prompt, max_tokens=512, temperature=0.7)

    with Timer("Extract Citations"):
        citations = []
        for idx, chunk in enumerate(context):
            tag = f"[{idx+1}]"
            if tag in answer_text:
                citations.append(Citation(
                    text=(chunk.get("ocr_text") or chunk.get("text") or "")[:200] + "...",
                    source=chunk.get("source"),
                    page=int(chunk.get("page") or 0),
                    chunk_id=chunk.get("chunk_id"),
                    confidence=float(chunk.get("score") or 0.0)
                ))
        print(f"    Extracted {len(citations)} citations")

    return {"answer": answer_text, "citations": citations}

# ---------------------------------------------------------------------------
# Workflow nodes
# ---------------------------------------------------------------------------
def retrieval_node(state: RAGState) -> RAGState:
    state["context"] = hybrid_search(state["project_id"], state["query"], top_k=state.get("top_k", Config.TOP_K))
    return state

def generation_node(state: RAGState) -> RAGState:
    res = generate_cited_answer(state["project_id"], state["query"], state["context"])
    state["answer"] = res["answer"]
    state["citations"] = res["citations"]
    return state

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    project_id: str = Form(...),
    chat_id: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    print("\n" + "="*80)
    print(f"📤 NEW UPLOAD: {file.filename}  (project={project_id}, chat={chat_id})")
    print("="*80)
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
            if file_ext == 'pdf':
                chunks = process_pdf(str(file_path))
            else:
                chunks = process_image(str(file_path), file.filename)
            store_in_vectordb(chunks, document_id, file.filename, project_id, chat_id)

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
    print("\n" + "="*80)
    print(f"📥 NEW QUERY: project={req.project_id} query='{req.query}' chat={req.chat_id}")
    print("="*80)
    start = datetime.now()

    try:
        with Timer("TOTAL QUERY TIME"):
            state: RAGState = {"project_id": req.project_id, "query": req.query, "context": [], "answer": "", "citations": [], "top_k": req.top_k}
            with Timer("Retrieval Phase"):
                state = retrieval_node(state)
            with Timer("Generation Phase"):
                state = generation_node(state)

        elapsed = (datetime.now() - start).total_seconds()
        print(f"\n✅ Query completed in {elapsed:.3f}s")
        print("="*80 + "\n")

        return QueryResponse(query=req.query, answer=state["answer"], citations=state["citations"], processing_time=elapsed)
    except Exception as e:
        print(f"❌ Query error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0-projects",
        "models": {"slm": Config.SLM_MODEL, "llm": Config.LLM_MODEL, "embedder": Config.EMBED_MODEL, "clip": Config.CLIP_MODEL},
        "named_vector_mode": USE_NAMED_VECTORS
    }

@app.get("/debug/ollama")
async def debug_ollama():
    try:
        with Timer("Ollama Debug Check"):
            models = get_available_models()
            test = call_ollama(Config.SLM_MODEL, "Say hello", max_tokens=10)
        return {"status": "healthy", "ollama_url": Config.OLLAMA_URL, "available_models": models, "test_generation": test[:100]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/qdrant")
async def debug_qdrant():
    try:
        # list collections
        collections = qdrant_client.get_collections().collections
        return {"status": "healthy", "collections": [c.name for c in collections], "bm25_projects": list(bm25_texts_by_project.keys())}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Startup banner
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*80)
    print("🚀 AI Service (project-scoped Qdrant + BM25)")
    print("="*80)
    print(f"📍 Qdrant: {Config.QDRANT_URL}")
    print(f"🤖 Ollama: {Config.OLLAMA_URL}")
    print(f"🔢 Embedder: {Config.EMBED_MODEL}")
    print(f"🎯 CLIP: {Config.CLIP_MODEL}")
    print(f"✅ Named-vector mode: {USE_NAMED_VECTORS}")
    print("="*80 + "\n")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
