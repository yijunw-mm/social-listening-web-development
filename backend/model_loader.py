from sentence_transformers import SentenceTransformer
from keybert import KeyBERT

"""just load the model once when fastapi start"""

encoder = SentenceTransformer("all-MiniLM-L6-v2")
kw_model = KeyBERT(model=encoder)
print("model successfully loaded and cached...")