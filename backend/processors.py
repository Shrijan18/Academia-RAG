import os
import re
import pandas as pd
import librosa
import numpy as np
import torch
import requests
import pdfplumber
import chardet
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import whisper_model, wav2vec_processor, wav2vec_model, DEVICE

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
    """
    Advanced PDF loader using pdfplumber for table-aware extraction.
    Includes automated semester tagging for metadata filtering.
    """
    docs = []
    print(f"Processing PDF: {file_path}")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # --- Semester Tagging Logic ---
                # This helps the RAG engine distinguish between 7th and 8th sem data
                semester_tag = "unknown"
                if re.search(r"Seventh Semester", text, re.IGNORECASE) or re.search(r"7th Semester", text, re.IGNORECASE):
                    semester_tag = "7"
                elif re.search(r"Eighth Semester", text, re.IGNORECASE) or re.search(r"8th Semester", text, re.IGNORECASE):
                    semester_tag = "8"
                elif re.search(r"Sixth Semester", text, re.IGNORECASE) or re.search(r"6th Semester", text, re.IGNORECASE):
                    semester_tag = "6"
                elif re.search(r"Fifth Semester", text, re.IGNORECASE) or re.search(r"5th Semester", text, re.IGNORECASE):
                    semester_tag = "5"

                # --- Table Extraction ---
                tables = page.extract_tables()
                table_text = ""
                if tables:
                    for table in tables:
                        for row in table:
                            # Join row elements with a pipe to preserve column structure
                            clean_row = [str(item).replace('\n', ' ') for item in row if item is not None]
                            table_text += " | ".join(clean_row) + "\n"
                
                # Combine standard text with the preserved table structure
                combined_content = f"Source: {os.path.basename(file_path)}\n"
                combined_content += f"Semester Context: {semester_tag}\n"
                combined_content += f"Page: {i+1}\n"
                combined_content += (text or "") + "\n\nTable Data:\n" + table_text
                
                # Append with semantic metadata
                docs.append(Document(
                    page_content=combined_content, 
                    metadata={
                        "source": file_path, 
                        "page": i+1, 
                        "semester": semester_tag,
                        "type": "pdf"
                    }
                ))
                
        return docs
    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
        return []

def load_csv(file_path):
    try:
        print(f"Processing CSV: {file_path}")
        df = pd.read_csv(file_path)
        
        documents = []
        safety_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        for index, row in df.iterrows():
            content = " | ".join([f"{col}: {val}" for col, val in row.items()])
            content = clean_text(content)
            
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
    try:
        print(f"Processing Audio: {file_path}")

        result = whisper_model.transcribe(
            file_path, 
            word_timestamps=True,
            verbose=False,
            fp16=(DEVICE.type == "cuda") 
        )

        audio, sr = librosa.load(file_path, sr=16000)
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

def load_txt(file_path):
    try:
        print(f"Processing Text: {file_path}")
        
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
        
        text = raw_data.decode(encoding)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
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

def extract_text_iteratively(start_url, max_pages=10, max_depth=1):
    visited_links = set()
    queue = deque([(start_url, 0)])
    documents = []
    
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
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            downloaded = trafilatura.fetch_url(url)
            clean_text_content = trafilatura.extract(downloaded, include_comments=False, include_tables=True)

            if clean_text_content:
                chunks = splitter.split_text(clean_text_content)
                for chunk in chunks:
                    documents.append(Document(
                        page_content=chunk,
                        metadata={
                            "source": url,
                            "type": "web",
                            "depth": depth
                        }
                    ))

            if depth < max_depth:
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    nested_url = urljoin(url, link["href"])
                    if nested_url.startswith(start_url) and nested_url not in visited_links:
                        queue.append((nested_url, depth + 1))

        except Exception as e:
            print(f"Error fetching {url}: {e}")

    return documents