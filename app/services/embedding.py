from sentence_transformers import SentenceTransformer

# Model ek baar load hoga jab app start hogi (baar baar load nahi hoga)
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embeddings(chunks: list[str]):
    """
    Given a list of text chunks, return their vector embeddings.
    """
    embeddings = model.encode(chunks, convert_to_numpy=True)
    return embeddings