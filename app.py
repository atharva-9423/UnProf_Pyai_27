import os
import tempfile
import warnings

from dotenv import load_dotenv
load_dotenv()  

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

import streamlit as st
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(
    page_title="Document AI — Chat with your Files",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Hide default Streamlit top bar */
    #MainMenu, footer, header { visibility: hidden; }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #0f0f0f;
        border-right: 1px solid #1e1e1e;
    }
    [data-testid="stSidebar"] * {
        color: #e5e5e5 !important;
    }

    /* Sidebar heading */
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
    }
    .sidebar-subtitle {
        font-size: 0.75rem;
        color: #888 !important;
        margin-bottom: 1.5rem;
    }

    /* Uploaded file badge */
    .file-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 0.75rem;
        color: #ccc !important;
        margin-bottom: 6px;
        width: 100%;
    }
    .file-badge-dot {
        width: 7px;
        height: 7px;
        background: #22c55e;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* Main area */
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -1px;
        color: #111827;
        margin-bottom: 0;
    }
    .main-subtitle {
        color: #9ca3af;
        font-size: 0.9rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* Chat messages */
    .stChatMessage {
        background: transparent !important;
        border-bottom: 1px solid #f3f4f6;
        padding-bottom: 1rem;
    }

    /* Chat input */
    .stChatInputContainer {
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
    }

    /* Status pill */
    .status-ready {
        display: inline-block;
        background: #f0fdf4;
        color: #16a34a;
        border: 1px solid #bbf7d0;
        border-radius: 99px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .status-empty {
        display: inline-block;
        background: #fefce8;
        color: #ca8a04;
        border: 1px solid #fde68a;
        border-radius: 99px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Booting AI engine...")
def load_base_components():
    if "GEMINI_API_KEY" not in os.environ:
        st.error("Please set the GEMINI_API_KEY environment variable before starting the app.")
        st.stop()

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    docs_folder = "documents"
    all_splits = []
    if os.path.exists(docs_folder):
        loader = DirectoryLoader(docs_folder, glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        if docs:
            all_splits = text_splitter.split_documents(docs)

    from langchain_core.documents import Document
    if not all_splits:
        all_splits = [Document(page_content="Welcome! Please upload a document to get started.")]

    vectorstore = FAISS.from_documents(all_splits, embeddings)

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        google_api_key=os.environ["GEMINI_API_KEY"]
    )

    return embeddings, text_splitter, vectorstore, llm


def build_rag_chain(vectorstore, llm):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    def get_contextualized_question(inputs):
        history = inputs.get("chat_history", [])
        if not history:
            return inputs["input"]
        last_human = ""
        for role, text in reversed(history):
            if role == "human":
                last_human = text
                break
        return f"{last_human} {inputs['input']}"

    qa_system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following retrieved context to answer the question. "
        "If you don't know the answer from the context, say so honestly. "
        "Keep the answer concise — three sentences maximum.\n\n"
        "Context: {context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    chain = (
        RunnablePassthrough.assign(standalone_question=get_contextualized_question)
        | RunnablePassthrough.assign(
            context=lambda x: "\n\n".join(
                doc.page_content for doc in retriever.invoke(x["standalone_question"])
            )
        )
        | qa_prompt
        | llm
        | StrOutputParser()
    )
    return chain


embeddings, text_splitter, vectorstore, llm = load_base_components()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "langchain_history" not in st.session_state:
    st.session_state.langchain_history = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = vectorstore

with st.sidebar:
    st.markdown('<p class="sidebar-title">📄 Document AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-subtitle">Upload files to chat with them</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload a PDF or TXT file",
        type=["pdf", "txt"],
        help="The file will be automatically indexed and added to your chatbot's knowledge base.",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        if uploaded_file.name not in st.session_state.uploaded_files:
            with st.spinner(f"📥 Indexing **{uploaded_file.name}**..."):
                try:
                    suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".txt"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    if suffix == ".pdf":
                        loader = PyPDFLoader(tmp_path)
                    else:
                        loader = TextLoader(tmp_path)

                    docs = loader.load()
                    splits = text_splitter.split_documents(docs)

                    st.session_state.vectorstore.add_documents(splits)
                    st.session_state.uploaded_files.append(uploaded_file.name)

                    os.remove(tmp_path)
                    st.success(f"✅ Indexed {len(splits)} chunks!")

                except Exception as e:
                    st.error(f"Failed to process file: {e}")

    if st.session_state.uploaded_files:
        st.markdown("**Indexed Documents**")
        for fname in st.session_state.uploaded_files:
            st.markdown(
                f'<div class="file-badge"><span class="file-badge-dot"></span>{fname}</div>',
                unsafe_allow_html=True
            )

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.langchain_history = []
        st.rerun()

st.markdown('<p class="main-title">Chat with your Documents</p>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Ask anything. The AI searches your uploaded files for answers.</p>', unsafe_allow_html=True)

if st.session_state.uploaded_files:
    files_count = len(st.session_state.uploaded_files)
    st.markdown(f'<span class="status-ready">● {files_count} file(s) indexed — Ready</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="status-empty">● No files uploaded — Using default knowledge base</span>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if query := st.chat_input("Ask a question about your documents..."):

    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    chain = build_rag_chain(st.session_state.vectorstore, llm)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            for chunk in chain.stream({
                "input": query,
                "chat_history": st.session_state.langchain_history
            }):
                full_response += chunk
                placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.langchain_history.append(("human", query))
            st.session_state.langchain_history.append(("ai", full_response))

        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
