'''
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config import API_KEY
import database
from flashrank import Ranker, RerankRequest

# Initialize FlashRank (Optimized for CPU speed)
ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="opt_models")
'''
import os
import time
from dotenv import load_dotenv # <--- ADD THIS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
# Ensure config.py or this file calls load_dotenv()
load_dotenv() 

from config import API_KEY 
import database
from flashrank import Ranker, RerankRequest

# Initialize FlashRank (Optimized for CPU speed)
ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir="opt_models")

# DEBUG: Verify the key is actually loaded
if not API_KEY:
    print("❌ ERROR: API_KEY is empty! Check your .env file.")
else:
    print(f"✅ API_KEY loaded (Starts with: {API_KEY[:4]}...)")


def rerank_results(query, retrieved_docs, top_n=5):
    """
    High-speed CPU reranking using FlashRank.
    """
    if not retrieved_docs:
        return [], []
        
    # Convert LangChain docs to FlashRank format
    passages = []
    for i, doc in enumerate(retrieved_docs):
        passages.append({
            "id": i,
            "text": doc.page_content,
            "meta": doc.metadata
        })
    
    rerank_request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(rerank_request)
    
    reranked_docs = []
    scores = []
    
    for res in results[:top_n]:
        # Map back to original docs using the result text
        original_doc = next(d for d in retrieved_docs if d.page_content == res['text'])
        reranked_docs.append(original_doc)
        scores.append(res['score'])
        
    return reranked_docs, scores

# Global Memory Storage (Short-Term Memory)
chat_history = []
MAX_HISTORY_MESSAGES = 6 # Keep the last 6 exchanges in full detail
MEMORY_SUMMARY = ""      # Stores the distilled "Sticky Note" recap

def get_history_context():
    """Formats history for the prompt, including the summary recap."""
    global MEMORY_SUMMARY, chat_history
    history_str = ""
    if MEMORY_SUMMARY:
        history_str += f"[Previous Summary Recap: {MEMORY_SUMMARY}]\n\n"
    
    for turn in chat_history:
        history_str += f"User: {turn['user']}\nAssistant: {turn['bot']}\n"
    return history_str

def summarize_history():
    """Distills old messages into a summary to save tokens."""
    global chat_history, MEMORY_SUMMARY
    if len(chat_history) <= MAX_HISTORY_MESSAGES:
        return

    print("STM: Memory limit reached. Summarizing old context...")
    # Extract the messages to be summarized (all but the last 2)
    to_summarize = chat_history[:-2]
    content = "\n".join([f"U: {t['user']} A: {t['bot']}" for t in to_summarize])
    
    summarizer_prompt = f"""
    Distill the following conversation into a 2-sentence summary of the key facts and user needs.
    Current Recap: {MEMORY_SUMMARY}
    New exchanges: {content}
    """
    
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", api_key=API_KEY)
    try:
        response = llm.invoke(summarizer_prompt)
        MEMORY_SUMMARY = response.content
        # Keep only the most recent 2 exchanges in full detail
        chat_history = chat_history[-2:]
    except Exception as e:
        print(f"Summarization error: {e}")

def chatbot(query):
    """
    Optimized RAG Pipeline with STM.
    """
    greetings = ['hi', 'hello', 'hey', 'good morning', 'who are you']
    if query.lower() in greetings:
        return {
            "response": "Hello! I am Academia RAG. I have indexed your university regulations and scripts. How can I help you today?",
            "sources": []
        }

    global chat_history
    if database.text_db is None:
        return {"error": "DB_EMPTY", "answer": "Knowledge Base is empty.", "sources": []}

    start_time = time.time()
    history_context = get_history_context()

    # 1. Similarity Search
    candidates = database.text_db.similarity_search(query, k=20)
    search_time = time.time() - start_time

    # 2. Reranking
    rerank_start = time.time()
    reranked_docs, scores = rerank_results(query, candidates, top_n=10)
    rerank_time = time.time() - rerank_start

    # 3. Context Construction
    context_text = "\n\n".join([f"[{d.metadata.get('source', 'Unknown')}]\n{d.page_content}" for d in reranked_docs])

    print("HISTORY:\n", history_context, flush=True)
    print("\nCONTEXT:\n", context_text, flush=True)
    print("\nUSER QUERY:\n", query, flush=True)

    
    # 4. LLM Generation with Memory
    prompt = ChatPromptTemplate.from_template("""
    You are Academia RAG, a high-precision Academic Assistant for Bhilai Institute of Technology.
    Your goal is to provide DIRECT answers extracted ONLY from the CURRENT DOCUMENT CONTEXT.

    STRICT DATA INTEGRITY RULES:
    1. If the context does not contain the specific 'Subject Name' or 'Credits' for the requested semester, state: "The specific subjects for this semester are not present in my current search results." 
    2. NEVER invent or guess subject names (e.g., do not guess 'PHP' or 'Python' unless they appear in the {context}).
    3. PRIORITIZATION: If a .pdf file and a .txt file are both in the context, extract data from the .pdf and only use the .txt for general instructions or URLs.

    SYLLABUS & CREDIT EXTRACTION:
    1. Look for patterns like "Subject Code", "Subject Name", "L-T-P", and "Credits".
    2. If you find a table, translate it exactly into a Markdown table.
    3. If the user asks for "6th Semester", and the context contains "7th_8th_Sem.pdf", DO NOT use that file to answer the 6th-semester query.

    RESPONSE STRUCTURE:
    - [Answer from Context]
    - [Markdown Table of Subjects/Credits if found]
    - [Source Attribution: Mention exactly which file you used]
    - [Direct Download Link Reference]

    RECAP OF OLDER CONVERSATION (Memory):
    {history}

    CURRENT DOCUMENT CONTEXT:
    {context}

    USER QUESTION: {query}
    """)

    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", api_key=API_KEY)
    chain = prompt | llm
    
    try:
        gen_start = time.time()
        response = chain.invoke({
            "history": history_context,
            "context": context_text, 
            "query": query
        })
        gen_time = time.time() - gen_start
        
        # 5. Update Memory (Strip sources, save only Q&A)
        chat_history.append({"user": query, "bot": response.content})
        summarize_history() # Check if we need to compact memory

        sources = [{
            "content": doc.page_content,
            "score": float(score),
            "metadata": doc.metadata
        } for doc, score in zip(reranked_docs, scores)]

        return {"answer": response.content, "sources": sources}
    except Exception as e:
        return {"error": str(e), "answer": "Generation Error.", "sources": []}
