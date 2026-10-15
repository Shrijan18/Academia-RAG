import os
import torch
import warnings
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from .env
load_dotenv()

# Configuration / Constants
API_KEY = os.getenv("GOOGLE_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {DEVICE}")

# Embeddings Model (lightweight ~90MB, essential for RAG retrieval)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Lazy model singletons for audio (only loaded on demand if an audio file is ingested)
_whisper_model = None
_wav2vec_processor = None
_wav2vec_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("Loading Whisper model...")
        _whisper_model = whisper.load_model("base", device=DEVICE)
    return _whisper_model

def get_wav2vec():
    global _wav2vec_processor, _wav2vec_model
    if _wav2vec_processor is None or _wav2vec_model is None:
        from transformers import Wav2Vec2Processor, Wav2Vec2Model
        print("Loading Wav2Vec2 model...")
        _wav2vec_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
        _wav2vec_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h").to(DEVICE)
    return _wav2vec_processor, _wav2vec_model