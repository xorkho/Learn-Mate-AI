import faiss
import numpy as np
import pickle
import os

FAISS_DIR = "app/faiss_indexes"
os.makedirs(FAISS_DIR, exist_ok=True)

def get_index_path(document_id: int) -> str:
    return f"{FAISS_DIR}/doc_{document_id}.index"

def get_chunks_path(document_id: int) -> str:
    return f"{FAISS_DIR}/doc_{document_id}_chunks.pkl"


def save_to_faiss(document_id: int, chunks: list[str], embeddings: np.ndarray):
    """
    Create a FAISS index for a document and save it along with the raw chunks
    (chunks needed later to map search results back to actual text).
    """
    dimension = embeddings.shape[1]   # 384 for all-MiniLM-L6-v2
    index = faiss.IndexFlatL2(dimension)   # simple L2 distance index
    index.add(embeddings)

    # Save FAISS index to disk
    faiss.write_index(index, get_index_path(document_id))

    # Save chunks separately (FAISS index sirf vectors store karta hai, text nahi)
    with open(get_chunks_path(document_id), "wb") as f:
        pickle.dump(chunks, f)


def search_faiss(document_id: int, query_embedding: np.ndarray, top_k: int = 3) -> list[str]:
    """
    Search a document's FAISS index for the top_k most relevant chunks.
    """
    index_path = get_index_path(document_id)
    chunks_path = get_chunks_path(document_id)

    if not os.path.exists(index_path):
        return []

    index = faiss.read_index(index_path)

    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)

    query_embedding = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(query_embedding, top_k)

    results = [chunks[i] for i in indices[0] if i < len(chunks)]
    return results

def get_all_chunks(document_id: int) -> list[str]:
    """
    Return all stored chunks for a document (used for summary/quiz,
    where we need the whole document context, not just similarity search).
    """
    chunks_path = get_chunks_path(document_id)

    if not os.path.exists(chunks_path):
        return []

    with open(chunks_path, "rb") as f:
        chunks = pickle.load(f)

    return chunks