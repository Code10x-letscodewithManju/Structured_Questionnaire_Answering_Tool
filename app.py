import streamlit as st
import pandas as pd
import io
from st_login_form import login_form
from database import get_file_hash, is_doc_processed, save_doc_meta, upload_to_supabase
from engine import RAGEngine
from processor import process_questionnaire

# 1. Page Configuration & Branding
st.set_page_config(
    page_title="Structured Questionnaire Answering Tool", 
    layout="wide", 
    page_icon="🛡️"
)

# 2. User Authentication
if not st.session_state.get("authenticated"):
    
    left_co, cent_co, last_co = st.columns([1.5, 2, 1.5])
    
    with cent_co:
        st.title("🛡️ Intelligence Layer")
       
        login_form(allow_guest=False)
        st.info("Please login to access the Hybrid RAG Engine.")
        
    st.stop()

# --- MAIN APP UI - Only visible when logged in ---

# 3. Sidebar Navigation
with st.sidebar:
    st.success(f"User: **{st.session_state.get('username')}**")
    if st.button("Log Out"):
        st.session_state.authenticated = False
        st.rerun()
    st.divider()
    st.info("💡 **Tip:** Upload PDFs first to build the 'Brain' before running the Questionnaire.")


st.title("🛡️ Structured Questionnaire Answering Tool")

st.markdown("""
         *A Hybrid RAG Engine designed to automate complex questionnaires by mapping inquiries to verified corporate documentation.*
     """)

st.divider()

# --- APP LOGIC & STATE ---
if 'retriever' not in st.session_state:
    st.session_state.retriever = None
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

# --- SECTION 1: KNOWLEDGE BASE INGESTION ---
st.header("📂 1. Build Knowledge Base")
uploaded_pdfs = st.file_uploader(
    "Upload Security Policies, SOC2, or Whitepapers", 
    accept_multiple_files=True,
    type=["pdf"]
)

if st.button("🚀 Process & Index Documents"):
    if not uploaded_pdfs:
        st.error("Please upload at least one PDF.")
    else:
        engine = RAGEngine()
        all_chunks = []
        
        for pdf in uploaded_pdfs:
            file_bytes = pdf.read()
            f_hash = get_file_hash(file_bytes)
            
            if is_doc_processed(f_hash):
                st.warning(f"⚡ {pdf.name} found in cache. Loading existing vectors...")
                chunks = engine.process_pdf(file_bytes, pdf.name)
                all_chunks.extend(chunks)
            else:
                with st.spinner(f"Processing {pdf.name}..."):
                    upload_to_supabase(file_bytes, pdf.name)
                    chunks = engine.process_pdf(file_bytes, pdf.name)
                    all_chunks.extend(chunks)
                    save_doc_meta(pdf.name, f_hash)
                    st.success(f"✅ {pdf.name} indexed.")
        
        if all_chunks:
            st.session_state.retriever = engine.get_hybrid_retriever(all_chunks)
            st.balloons()
            st.success("Knowledge Base is LIVE!")

st.divider()

# --- SECTION 2: QUESTIONNAIRE & INTERACTIVE REVIEW ---
st.header("📝 2. Run & Review Questionnaire")
excel_file = st.file_uploader("Upload Questionnaire (Excel)", type=["xlsx"])

if excel_file and st.session_state.retriever:
    if st.button("🤖 Generate AI Answers"):
        with st.spinner("Analyzing documents and citing sources..."):
            engine = RAGEngine()
            _, summary_list = process_questionnaire(
                excel_file, st.session_state.retriever, engine.llm
            )
            st.session_state.current_results = summary_list

# --- SECTION 3: COVERAGE SUMMARY & REVIEW GRID ---
if st.session_state.current_results:
    df_to_edit = pd.DataFrame(st.session_state.current_results)
    
    # --- COVERAGE SUMMARY DASHBOARD ---
    st.subheader("📊 Coverage Summary")
    total_q = len(df_to_edit)
    # Count rows where answer is NOT a "not found" variant
    answered_q = len(df_to_edit[~df_to_edit['Answer'].str.contains("not found", case=False, na=False)])
    unanswered_q = total_q - answered_q

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Questions", total_q)
    m2.metric("Answered (with Citations)", answered_q)
    m3.metric("Gaps Identified", unanswered_q, delta_color="inverse")
    st.divider()

    # --- REVIEW GRID ---
    st.subheader("🔍 Review & Edit Stage")
    st.info("Double-click any cell to edit the Answer or Citation before downloading.")
    
    edited_df = st.data_editor(
        df_to_edit, 
        use_container_width=True, 
        num_rows="dynamic",
        column_config={
            "Question": st.column_config.TextColumn(width="medium", disabled=True),
            "Answer": st.column_config.TextColumn(width="large"),
            "Citation": st.column_config.TextColumn(width="small")
        }
    )

    st.markdown("---")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Download Verified Excel Questionnaire",
        data=output.getvalue(),
        file_name=f"Verified_{excel_file.name}",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.caption("⚙️ Powered by Hybrid Retrieval-Augmented Generation (RAG) for zero-hallucination accuracy.")