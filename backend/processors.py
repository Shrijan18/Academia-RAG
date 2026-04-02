import pandas as pd
import librosa
import numpy as np
import torch
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import whisper_model, wav2vec_processor, wav2vec_model, DEVICE

import re

def clean_text(text):
    """
    Sanitizes text to improve embedding quality.
    Removes redundant whitespace and invisible characters.
    """
    if not text:
        return ""
    # Replace multiple newlines/tabs with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def load_pdf(file_path):
    try:
        print(f"Processing PDF: {file_path}")
        loader = PyMuPDFLoader(file_path)
        pages = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, # ~250 tokens, ideal for MiniLM
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        docs = splitter.split_documents(pages)
        
        # Sanitize and filter
        for doc in docs:
            doc.page_content = clean_text(doc.page_content)
            
        return [d for d in docs if len(d.page_content) > 20] # Filter junk
    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
        return []

def load_csv(file_path):
    try:
        print(f"Processing CSV: {file_path}")
        df = pd.read_csv(file_path)
        
        documents = []
        # If a row is massive, we might need a safety splitter
        safety_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        for index, row in df.iterrows():
            content = " | ".join([f"{col}: {val}" for col, val in row.items()])
            content = clean_text(content)
            
            # Create documents (split if row is abnormally long)
            row_docs = safety_splitter.create_documents(
                [content], 
                metadatas=[{"source": file_path, "row": index, "type": "csv"}]
            )
            documents.extend(row_docs)
            
        return documents
    except Exception as e:
        print(f"Error loading CSV {file_path}: {e}")
        return []
def load_audio(file_path):
    """
    Optimized Audio processor. 
    Returns transcribed text as Documents and a global audio feature embedding.
    """
    try:
        print(f"Processing Audio: {file_path}")

        # 1. High-quality Transcription with Whisper
        # Using beam_size=5 for better accuracy, and fp16 adjustment based on device
        result = whisper_model.transcribe(
            file_path, 
            word_timestamps=True,
            verbose=False,
            fp16=(DEVICE.type == "cuda") 
        )

        # 2. Extract global audio features with Wav2Vec2 (Memory Safe)
        audio, sr = librosa.load(file_path, sr=16000)

        # If audio is very long, we take a representative 30s sample from the middle 
        # to avoid OOM while still capturing the acoustic 'vibe' of the file.
        max_samples = 16000 * 30 
        if len(audio) > max_samples:
            start_sample = len(audio) // 2 - (max_samples // 2)
            audio_sample = audio[start_sample : start_sample + max_samples]
        else:
            audio_sample = audio

        inputs = wav2vec_processor(audio_sample, sampling_rate=16000, return_tensors="pt", padding=True)
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

        with torch.no_grad():
            audio_embedding = wav2vec_model(**inputs).last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

        # 3. Create Documents from segments
        segments = result.get("segments", [])
        documents = []

        for seg in segments:
            start, end = seg['start'], seg['end']
            text = seg['text'].strip()

            if not text:
                continue

            doc = Document(
                page_content=f"[{int(start // 60):02d}:{int(start % 60):02d}] {text}",
                metadata={
                    "source": file_path,
                    "start_time": start,
                    "end_time": end,
                    "type": "audio"
                }
            )
            documents.append(doc)

        return documents, audio_embedding
    except Exception as e:
        print(f"Error loading Audio {file_path}: {e}")
        return [], None

import chardet

def load_txt(file_path):
    """
    Robust text loader with automatic encoding detection.
    Uses RecursiveCharacterTextSplitter for RAG-friendly chunking.
    """
    try:
        print(f"Processing Text: {file_path}")
        
        # 1. Detect encoding (essential for production-grade loaders)
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
        
        text = raw_data.decode(encoding)
        
        # 2. Split text into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        # 3. Create Documents
        chunks = splitter.split_text(text)
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append(Document(
                page_content=chunk,
                metadata={
                    "source": file_path,
                    "type": "txt",
                    "chunk": i
                }
            ))
            
        return documents
    except Exception as e:
        print(f"Error loading Text {file_path}: {e}")
        return []

import trafilatura

def extract_text_iteratively(start_url, max_pages=10, max_depth=1):
    """
    Optimized Web Scraper for RAG.
    Uses trafilatura for 'main content' extraction (ignoring ads/nav).
    Returns a list of LangChain Document objects.
    """
    visited_links = set()
    queue = deque([(start_url, 0)])
    documents = []
    
    # Common headers to avoid 403 Forbidden
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    print(f"Scraping: {start_url} (Max pages: {max_pages})")

    while queue and len(visited_links) < max_pages:
        url, depth = queue.popleft()
        if depth > max_depth or url in visited_links:
            continue

        visited_links.add(url)
        try:
            # 1. Fetch content
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # 2. Extract clean content using trafilatura
            # This is much better than soup.get_text() as it targets 'main' article text
            downloaded = trafilatura.fetch_url(url)
            clean_text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)

            if clean_text:
                # 3. Create chunks and Documents
                chunks = splitter.split_text(clean_text)
                for chunk in chunks:
                    documents.append(Document(
                        page_content=chunk,
                        metadata={
                            "source": url,
                            "type": "web",
                            "depth": depth
                        }
                    ))

            # 4. Find nested links (only if depth permits)
            if depth < max_depth:
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    nested_url = urljoin(url, link["href"])
                    # Only follow internal links
                    if nested_url.startswith(start_url) and nested_url not in visited_links:
                        queue.append((nested_url, depth + 1))

        except Exception as e:
            print(f"Error fetching {url}: {e}")

    return documents
