import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL")
    supabase_key: str = os.getenv("SUPABASE_KEY")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")

    # Configuración de autenticación de prueba
    test_email: str = "lokilskdij@gmail.com"
    test_password: str = "Passw0rd!"

settings = Settings()

