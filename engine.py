from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from config import OPENAI_API_KEY, PINECONE_INDEX_NAME
import fitz  # PyMuPDF for high-accuracy PDF parsing

class RAGEngine:
    def __init__(self):
        # Using 1536-dim embeddings to match our Pinecone index
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # GPT-4o-mini is cost-effective and follows strict formatting instructions (OPENSOURCE models rom HF can also be used here, but may require more prompt engineering to avoid hallucinations)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
    def process_pdf(self, file_bytes, filename):
        """Extracts text and attaches page-level metadata for precise citations."""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        chunks = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                chunks.append(Document(
                    page_content=text,
                    metadata={"source": filename, "page": page_num + 1}
                ))
        return chunks

    def get_hybrid_retriever(self, all_docs):
        """Creates a Hybrid Search engine (Semantic + Keyword) for better accuracy."""
        # 1. Semantic Search (Dense Vectors) via Pinecone
        vectorstore = PineconeVectorStore.from_documents(
            all_docs, self.embeddings, index_name=PINECONE_INDEX_NAME
        )
        
        # 2. Keyword Search (Sparse) via BM25 (Ideal for technical terms/acronyms)
        bm25_retriever = BM25Retriever.from_documents(all_docs)
        bm25_retriever.k = 2 # Retrieve top 2 keyword matches
        
        # 3. Ensemble (Hybrid): Combines results using Reciprocal Rank Fusion
        return EnsembleRetriever(
            retrievers=[bm25_retriever, vectorstore.as_retriever(search_kwargs={"k": 2})],
            weights=[0.4, 0.6] # Give slightly more weight to semantic meaning
        )
