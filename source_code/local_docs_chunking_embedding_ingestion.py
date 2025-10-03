#################################################################################################################################################################
###############################   1.  IMPORTING MODULES AND INITIALIZING VARIABLES   ############################################################################
#################################################################################################################################################################

from dotenv import load_dotenv
import os
import json
import pandas as pd
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from uuid import uuid4
import shutil
import time


load_dotenv()

###############################   INITIALIZE EMBEDDINGS MODEL  #################################################################################################

embeddings = OllamaEmbeddings(
    model=os.getenv("EMBEDDING_MODEL"),
)

###############################   DELETE CHROMA DB IF EXISTS AND INITIALIZE   ##################################################################################

if os.path.exists(os.getenv("DATABASE_LOCATION")):
    shutil.rmtree(os.getenv("DATABASE_LOCATION"))

vector_store = Chroma(
    collection_name=os.getenv("COLLECTION_NAME"),
    embedding_function=embeddings,
    persist_directory=os.getenv("DATABASE_LOCATION"), 
)

###############################   INITIALIZE TEXT SPLITTER   ###################################################################################################

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

#################################################################################################################################################################
###############################   2.  PROCESSING THE JSON RESPONSE LINE BY LINE   ###############################################################################
#################################################################################################################################################################

###############################   FUNCTION TO EXTRACT RESPONSE LINE BY LINE   ###################################################################################



def load_dataset(file_path: str):
    """Load dataset supporting both full-file JSON (dict or list) and JSON Lines (JSONL)."""
    # Try full-file JSON first
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # If it's a mapping {name: content}
        if isinstance(data, dict):
            items = []
            for k, v in data.items():
                title = os.path.splitext(os.path.basename(k))[0]
                items.append({
                    "url": k,
                    "title": title,
                    "raw_text": v,
                })
            return items
        # If it's already a list of objects (e.g., Bright Data export)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        # Fallback to JSONL parsing
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    items.append(obj)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        return items

input_folder = os.getenv("DATASET_STORAGE_FOLDER") or "datasets"
input_file = os.getenv("DATASET_STORAGE_FILE_NAME") or "data.txt"
input_path = os.path.join(input_folder, input_file)
file_content = load_dataset(input_path)


#################################################################################################################################################################
###############################   3.  CHUNKING, EMBEDDING AND INGESTION   #######################################################################################
##################################################################################################################################################################

for line in file_content:

    url = line.get('url') or line.get('source') or line.get('file') or 'unknown'
    title = line.get('title') or os.path.basename(url)
    raw_text = line.get('raw_text') or line.get('content') or line.get('text') or ''
    if not raw_text:
        continue

    print(url)

    texts = text_splitter.create_documents([raw_text], metadatas=[{"source": url, "title": title}])

    uuids = [str(uuid4()) for _ in range(len(texts))]

    vector_store.add_documents(documents=texts, ids=uuids)