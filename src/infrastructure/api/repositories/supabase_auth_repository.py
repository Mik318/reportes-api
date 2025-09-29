from supabase import create_client
from typing import Optional

from src.config import settings
from src.domain.models import User
from src.domain.repositories import AuthRepository


class SupabaseAuthRepository(AuthRepository):
    def __init__(self):
        self.supabase = create_client(settings.supabase_url, settings.supabase_key)

    def get_user_from_token(self, token: str) -> Optional[User]:
        try:
            user_data = self.supabase.auth.get_user(token)
            if user_data and user_data.user:
                return User(id=user_data.user.id, email=user_data.user.email)
            return None
        except Exception:
            return None

    def sign_in_with_password(self, email: str, password: str) -> str:
        user = self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return user.session.access_token

