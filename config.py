import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Securely fetch API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "aegisgrad-index"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Safety check to ensure environment is ready
if not all([OPENAI_API_KEY, PINECONE_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("⚠️ WARNING: One or more API keys are missing in your .env file!")