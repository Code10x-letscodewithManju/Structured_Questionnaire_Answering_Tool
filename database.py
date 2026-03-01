import hashlib
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Initializing Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_file_hash(file_bytes):
    """Generates a SHA-256 fingerprint of the file to prevent redundant processing."""
    return hashlib.sha256(file_bytes).hexdigest()

def is_doc_processed(file_hash):
    """Checks if this specific file content has already been embedded in Pinecone."""
    res = supabase.table("processed_documents").select("file_hash").eq("file_hash", file_hash).execute()
    return len(res.data) > 0

def save_doc_meta(filename, file_hash):
    """Logs the processed file hash into the database."""
    supabase.table("processed_documents").insert({
        "filename": filename, 
        "file_hash": file_hash
    }).execute()

def upload_to_supabase(file_bytes, filename):
    """Uploads the raw PDF to Supabase Storage for permanent reference."""
    try:
        supabase.storage.from_("reference-docs").upload(
            path=filename, 
            file=file_bytes, 
            file_options={"upsert": "true"}
        )
    except Exception as e:
        print(f"Storage upload note: {e}") 


