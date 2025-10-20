from typing import Optional, Any

from postgrest import APIResponse
from supabase import create_client
from supabase_auth.errors import AuthApiError

from src.config import settings
from src.domain.models import User
from src.domain.repositories import AuthRepository
from src.domain.errors import InvalidCredentialsError, EmailNotConfirmedError


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
        try:
            user = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return user.session.access_token
        except AuthApiError as e:
            # Diferenciar cuando el email no ha sido confirmado
            msg = str(e).lower()
            if "email not confirmed" in msg or "not confirmed" in msg or "confirm" in msg:
                raise EmailNotConfirmedError()
            # Traducimos otros errores de Supabase a un error de dominio
            raise InvalidCredentialsError()
        except Exception as e:
            # Cualquier otro error inesperado
            print(f"Error inesperado durante el inicio de sesión: {e}")
            raise InvalidCredentialsError()

    def find_by_email(self, email: str) -> Optional[User]:
        """Busca un usuario por su email llamando a una función de la base de datos.

        Normaliza distintos formatos que puede devolver `response.data`:
        - lista (p. ej. [{'get_user_id_by_email': 'uuid'}])
        - dict (p. ej. {'get_user_id_by_email': 'uuid'})
        - valor escalar ('uuid')
        """
        try:
            response: APIResponse = self.supabase.rpc(
                "get_user_id_by_email", {"p_email": email}
            ).execute()

            data: Any = response.data
            user_id: Optional[Any] = None

            if isinstance(data, list):
                if len(data) == 0:
                    user_id = None
                else:
                    first = data[0]
                    if isinstance(first, dict):
                        # intentar varias claves comunes
                        user_id = first.get('get_user_id_by_email') or first.get('id') or first.get('user_id') or next(iter(first.values()), None)
                    else:
                        user_id = first
            elif isinstance(data, dict):
                user_id = data.get('get_user_id_by_email') or data.get('id') or data.get('user_id') or next(iter(data.values()), None)
            else:
                user_id = data

            if user_id:
                return User(id=str(user_id), email=email)

            return None

        except Exception as e:
            print(f"Error inesperado al buscar usuario por RPC: {e}")
            return None