# import basics
import os
import json
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv

# import streamlit
import streamlit as st

# import langchain
from langchain.agents import AgentExecutor
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

# load environment variables
load_dotenv()  

###############################   INITIALIZE EMBEDDINGS MODEL  #################################################################################################

embeddings = OllamaEmbeddings(
    model=os.getenv("EMBEDDING_MODEL"),
)

###############################   INITIALIZE CHROMA VECTOR STORE   #############################################################################################

vector_store = Chroma(
    collection_name=os.getenv("COLLECTION_NAME"),
    embedding_function=embeddings,
    persist_directory=os.getenv("DATABASE_LOCATION"), 
)


###############################   INITIALIZE CHAT MODEL   #######################################################################################################

llm = init_chat_model(
    os.getenv("CHAT_MODEL"),
    model_provider=os.getenv("MODEL_PROVIDER"),
    temperature=0
)

       


# pulling prompt from hub
prompt = PromptTemplate.from_template("""                                
You are a helpful assistant. You will be provided with a query and a chat history.
Your task is to retrieve relevant information from the vector store and provide a response.
For this you use the tool 'retrieve' to get the relevant information.
                                      
The query is as follows:                    
{input}

The chat history is as follows:
{chat_history}

Please provide a concise and informative response based on the retrieved information.
If you don't know the answer, say "I don't know" (and don't provide a source).
                                      
You can use the scratchpad to store any intermediate results or notes.
The scratchpad is as follows:
{agent_scratchpad}

For every piece of information you provide, also provide the source.

Return text as follows:

<Answer to the question>
Source: source_url
""")


# creating the retriever tool
@tool
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)

    serialized = ""

    for doc in retrieved_docs:
        serialized += f"Source: {doc.metadata['source']}\nContent: {doc.page_content}\n\n"

    return serialized

# combining all tools
tools = [retrieve]

# initiating the agent
agent = create_tool_calling_agent(llm, tools, prompt)

# create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ===== Chat history persistence helpers =====

def get_history_path() -> str:
    path = os.getenv("CHAT_HISTORY_FILE") or os.path.join("../datasets", "chat_history.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def load_all_records() -> list[dict]:
    """Load raw JSONL records from the history file (backward compatible)."""
    records: list[dict] = []
    path = get_history_path()
    if not os.path.exists(path):
        return records
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        records.append(obj)
                except json.JSONDecodeError:
                    continue
    except Exception:
        # ignore corrupted history silently
        pass
    return records


def list_sessions(records: list[dict]) -> list[dict]:
    """Aggregate sessions from records.
    Returns list of dicts: {chat_id, name, count, last_ts}
    Backward compatibility: messages without chat_id belong to a 'legacy' session.
    """
    sessions: dict[str, dict] = {}
    for r in records:
        chat_id = r.get("chat_id") or "legacy"
        chat_name = r.get("chat_name") or ("Legacy" if chat_id == "legacy" else "Unnamed Chat")
        ts = r.get("ts") or ""
        s = sessions.get(chat_id)
        if not s:
            sessions[chat_id] = {"chat_id": chat_id, "name": chat_name, "count": 0, "last_ts": ts}
            s = sessions[chat_id]
        role = r.get("role")
        if role in ("user", "assistant", "ai", "bot"):
            s["count"] += 1
        if chat_name:
            s["name"] = chat_name
        if ts and (not s["last_ts"] or ts > s["last_ts"]):
            s["last_ts"] = ts
    return sorted(sessions.values(), key=lambda x: x["last_ts"] or "", reverse=True)


def load_session_messages(records: list[dict], chat_id: str) -> list:
    msgs = []
    for r in records:
        rid = r.get("chat_id") or "legacy"
        if rid != chat_id:
            continue
        role = r.get("role")
        content = r.get("content", "")
        if not content:
            continue
        if role == "user":
            msgs.append(HumanMessage(content))
        elif role in ("assistant", "ai", "bot"):
            msgs.append(AIMessage(content))
    return msgs


def append_history(role: str, content: str, request_id: str | None = None, chat_id: str | None = None, chat_name: str | None = None) -> None:
    rec = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "role": role,
        "content": content,
    }
    if request_id:
        rec["request_id"] = request_id
    if chat_id:
        rec["chat_id"] = chat_id
    if chat_name:
        rec["chat_name"] = chat_name
    with open(get_history_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# initiating streamlit app
st.set_page_config(page_title="Personal Chatbot", page_icon="🦜", layout="wide")
# Header with logo and title on the same line
logo_col, title_col = st.columns([1, 12])
with logo_col:
    st.image("resources/images/personal_chatbot_ai_friend.png", width=32)
with title_col:
    st.title("Personal Chatbot")

# Load all records and available sessions
records = load_all_records()
sessions = list_sessions(records)

# Initialize session state for current chat
if "current_chat_id" not in st.session_state:
    if sessions:
        st.session_state.current_chat_id = sessions[0]["chat_id"]
        st.session_state.current_chat_name = sessions[0]["name"]
    else:
        st.session_state.current_chat_id = str(uuid4())
        st.session_state.current_chat_name = "New Chat"
if "loaded_chat_id" not in st.session_state:
    st.session_state.loaded_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for chat sessions
with st.sidebar:
    st.header("Chats")

    # New chat creation
    default_new_name = st.session_state.get("new_chat_name") or f"New Chat {datetime.now().strftime('%b %d %H:%M')}"
    new_name = st.text_input("New chat name", value=default_new_name, key="new_chat_name")
    if st.button("➕ New Chat"):
        st.session_state.current_chat_id = str(uuid4())
        st.session_state.current_chat_name = new_name.strip() or "New Chat"
        st.session_state.messages = []  # start without pulling any history
        st.session_state.loaded_chat_id = st.session_state.current_chat_id
        st.rerun()

    # Sessions list
    options = [f"{s['name']} ({s['count']})" for s in sessions]
    ids = [s["chat_id"] for s in sessions]
    idx = ids.index(st.session_state.current_chat_id) if st.session_state.current_chat_id in ids else (0 if ids else -1)
    selected = st.selectbox("All sessions", options, index=idx if idx >= 0 else None)
    if selected:
        sel_idx = options.index(selected)
        sel_id = ids[sel_idx]
        if sel_id != st.session_state.current_chat_id:
            st.session_state.current_chat_id = sel_id
            st.session_state.current_chat_name = sessions[sel_idx]["name"]
            st.session_state.messages = load_session_messages(records, sel_id)
            st.session_state.loaded_chat_id = sel_id
            st.rerun()

    # Rename current chat (kept in state, persisted on next message write)
    st.text_input("Chat name", key="current_chat_name", value=st.session_state.current_chat_name)

# Ensure current session messages are loaded once per session selection
if st.session_state.loaded_chat_id != st.session_state.current_chat_id:
    st.session_state.messages = load_session_messages(records, st.session_state.current_chat_id)
    st.session_state.loaded_chat_id = st.session_state.current_chat_id

# Display chat messages for the current session
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Input box uses current chat name for friendliness
user_question = st.chat_input(f"Message {st.session_state.current_chat_name}…")

# Handle user input
if user_question:
    request_id = str(uuid4())
    chat_id = st.session_state.current_chat_id
    chat_name = st.session_state.current_chat_name

    # Show and persist the user message
    with st.chat_message("user"):
        st.markdown(user_question)
        st.session_state.messages.append(HumanMessage(user_question))
        append_history("user", user_question, request_id, chat_id=chat_id, chat_name=chat_name)

    # Invoke the agent using only this session's history
    try:
        result = agent_executor.invoke({"input": user_question, "chat_history": st.session_state.messages, "chat_id": chat_id})
        ai_message = result.get("output", "")
        if not ai_message:
            ai_message = "I don't know."
    except Exception as e:
        ai_message = f"Sorry, something went wrong while generating a response. ({e})"

    # Show and persist the assistant message
    with st.chat_message("assistant"):
        st.markdown(ai_message)
        st.session_state.messages.append(AIMessage(ai_message))
        append_history("assistant", ai_message, request_id, chat_id=chat_id, chat_name=chat_name)

