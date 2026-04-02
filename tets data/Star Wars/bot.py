import pandas as pd
import whisper
import librosa
import numpy as np
import torch
import faiss
from transformers import Wav2Vec2Processor, Wav2Vec2Model
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from collections import deque
from sentence_transformers import CrossEncoder
from watchdog.observers import Observer
from langchain.schema import Document
from watchdog.events import FileSystemEventHandler
import time
import os
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")


API_key = ""
COHERE_API_KEY = ""
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load Whisper Model
whisper_model = whisper.load_model("base", device=device)

# Load Wav2Vec2 Model for audio embeddings
wav2vec_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
wav2vec_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h").to(device)

# Load BGE Reranker Model
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[-1].lower()

        print(f"🔄 File changed: {file_path}")

        if file_ext == ".pdf":
            update_pdf_embeddings(file_path)
        elif file_ext == ".csv":
            update_csv_embeddings(file_path)
        elif file_ext in [".wav", ".mp3"]:
            update_audio_embeddings(file_path)

def start_file_watcher(directory=filepath):
    observer = Observer()
    event_handler = FileChangeHandler()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

# Maintain a mapping of stored file embeddings
file_embedding_map = {}

def update_pdf_embeddings(file_path):
    global db
    print(f"📄 Updating FAISS for {file_path}")

    # Remove old embeddings from FAISS
    if file_path in file_embedding_map:
        db.delete(file_embedding_map[file_path])

    # Load and re-embed document
    pdf_docs = load_pdf(file_path)
    new_db = FAISS.from_documents(pdf_docs, embeddings)
    
    # Store new embeddings in FAISS
    file_embedding_map[file_path] = new_db.index.ntotal  # Track index positions
    db.merge_from(new_db)

def update_csv_embeddings(file_path):
    global db
    print(f"📊 Updating FAISS for {file_path}")

    if file_path in file_embedding_map:
        db.delete(file_embedding_map[file_path])

    csv_docs = load_csv(file_path)
    new_db = FAISS.from_documents(csv_docs, embeddings)

    file_embedding_map[file_path] = new_db.index.ntotal
    db.merge_from(new_db)

def update_audio_embeddings(file_path):
    global audio_text_db, audio_index
    print(f"🎙️ Updating FAISS for {file_path}")

    if file_path in file_embedding_map:
        audio_text_db.delete(file_embedding_map[file_path])
        audio_index.reset()  # Clear old audio embeddings

    audio_docs, audio_text_embeddings, audio_embedding = load_audio(file_path, embeddings)
    new_audio_text_db = FAISS.from_embeddings(list(zip([doc["page_content"] for doc in audio_docs], audio_text_embeddings)), embeddings)
    
    audio_text_db.merge_from(new_audio_text_db)
    audio_index.add(np.array([audio_embedding]))

    file_embedding_map[file_path] = new_audio_text_db.index.ntotal

#space

def load_pdf(file_path):
    pdf = PyPDFLoader(file_path)
    return pdf.load_and_split()

def load_csv(file_path):
    df = pd.read_csv(file_path)
    text_data = "\n".join(df.apply(lambda row: " | ".join(map(str, row)), axis=1))
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.create_documents([text_data])

def load_audio(file_path, embeddings):
    """Converts audio to text, extracts speaker identity & timestamps, and generates embeddings."""
    result = whisper_model.transcribe(file_path, word_timestamps=True)
    
    audio, sr = librosa.load(file_path, sr=16000)
    
    # Process audio with Wav2Vec2 for embeddings
    inputs = wav2vec_processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)
    
    # Send the inputs to the same device as the model
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        audio_embedding = wav2vec_model(**inputs).last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    
    # Extract sentences, timestamps, and speaker information
    segments = result.get("segments", [])
    
    audio_docs = []
    audio_embeddings = []
    
    for seg in segments:
        start, end = seg['start'], seg['end']
        text = seg['text']
        
        # Generate text embedding for each segment
        text_embedding = embeddings.embed_query(text)
        
        # Create a document-like format
        audio_doc = {
            "page_content": f"[{start:.2f}s - {end:.2f}s] {text}",
            "metadata": {"start": start, "end": end}
        }
        
        audio_docs.append(audio_doc)
        audio_embeddings.append(text_embedding)
    
    return audio_docs, np.array(audio_embeddings), audio_embedding


def extract_text_iteratively(start_url, max_depth=2):
    """Extracts text from a webpage and its nested links iteratively using a queue."""
    visited_links = set()
    queue = deque([(start_url, 0)])
    extracted_texts = []

    while queue:
        url, depth = queue.popleft()
        if depth > max_depth or url in visited_links:
            continue

        visited_links.add(url)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
                tag.extract()

            extracted_texts.append(soup.get_text(separator=" ", strip=True))

            # Add nested links to the queue
            for link in soup.find_all("a", href=True):
                nested_url = urljoin(url, link["href"])
                if nested_url.startswith(start_url):
                    queue.append((nested_url, depth + 1))

        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")

    return extracted_texts

def rerank_results(query, retrieved_docs):
    texts = [doc.page_content for doc in retrieved_docs]
    scores = reranker.predict([(query, text) for text in texts])
    sorted_data = sorted(zip(scores, retrieved_docs), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in sorted_data], sorted(scores, reverse=True)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
pdf_docs = load_pdf() #Function to load pdf
csv_docs = load_csv() #Function to load csv
audio_docs, audio_text_embeddings, audio_embedding = load_audio(embeddings) #Function to load AUDIO

# Store text data in FAISS
db = FAISS.from_documents(pdf_docs + csv_docs, embeddings)

# Store audio text embeddings separately
audio_text_db = FAISS.from_embeddings(list(zip([doc["page_content"] for doc in audio_docs], audio_text_embeddings)), embeddings)

# Store audio embeddings in FAISS
audio_index = faiss.IndexFlatL2(768)
audio_index.add(np.array([audio_embedding]))

def chatbot(query):
    docs = db.similarity_search(query)
    audio_docs = audio_text_db.similarity_search(query)

    # Merge retrieved results
    retrieved_docs = docs + audio_docs

    # Apply BGE Reranking
    reranked_docs, rerank_scores = rerank_results(query, retrieved_docs)

    # Use top reranked documents
    top_k = 5
    relevant_search = "\n".join([f"Score: {score:.4f} | {doc.page_content}" for doc, score in zip(reranked_docs[:top_k], rerank_scores[:top_k])])

    gem_prompt = "Use the following context to answer the question. If you don't know, say 'I don't know'."
    Input_prompt = f"{gem_prompt}\nContext: {relevant_search}\nUser Question: {query}"

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=API_key)
    result = llm.invoke(Input_prompt)

    print("\n🤖 AI Response:\n", result.content if hasattr(result, "content") else result)
    
    # Display Reranking Scores
    print("\n🔍 **Top Reranked Documents & Scores:**")
    for i in range(min(len(reranked_docs), top_k)):
        print(f"{i+1}. Score: {rerank_scores[i]:.4f} | {reranked_docs[i].page_content[:100]}...")  # Showing only the first 100 chars

    print("\nSuccess!!")

while True:
    query = input("Enter Query: ")
    if query == "exit":
        break
    chatbot(query)
