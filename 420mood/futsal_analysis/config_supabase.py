from supabase import create_client, Client

SUPABASE_URL = "https://jinmmonxjovoccejgwhk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imppbm1tb254am92b2NjZWpnd2hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1NTk3NzksImV4cCI6MjA2NTEzNTc3OX0.kapMvgvW-6fng-RhxZV_YFcLnxcXo9Bg2wpDWu_H-5g"

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)