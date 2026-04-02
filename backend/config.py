import os
import torch
import whisper
import warnings
from dotenv import load_dotenv
from transformers import Wav2Vec2Processor, Wav2Vec2Model
from sentence_transformers import CrossEncoder
from langchain_huggingface import HuggingFaceEmbeddings

# Suppress all warnings
# warnings.filterwarnings("ignore")

# Load environment variables from .env
load_dotenv()

# Configuration / Constants
API_KEY = os.getenv("GOOGLE_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- Model Singletons ---

print(f"Using device: {DEVICE}")

# Load Whisper Model
whisper_model = whisper.load_model("base", device=DEVICE)

# Load Wav2Vec2 Model for audio embeddings
wav2vec_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
wav2vec_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h").to(DEVICE)

# Load BGE Reranker Model
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Embeddings Model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
