from typing import Optional, Any
import logging

from postgrest import APIResponse
from supabase import create_client
from supabase_auth.errors import AuthApiError
import httpx

from src.config import settings
from src.domain.models import User
from src.domain.repositories import AuthRepository
from src.domain.errors import InvalidCredentialsError, EmailNotConfirmedError, UserAlreadyExistsError

logger = logging.getLogger(__name__)


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

    def sign_in_with_password(self, email: str, password: str) -> dict:
        """Inicia sesión con email/password y devuelve dict con access_token y refresh_token (si está disponible)."""
        try:
            user = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            # Normalizar posibles formas de respuesta
            session = None

            # 1) Si la respuesta es un dict
            if isinstance(user, dict):
                # Forma común: {'data': {'session': {...}, 'user': {...}}, 'error': None}
                if 'session' in user and user['session']:
                    session = user['session']
                elif 'data' in user and isinstance(user['data'], dict):
                    # data puede contener session o access_token directo
                    data = user['data']
                    if 'session' in data and data['session']:
                        session = data['session']
                    elif 'access_token' in data:
                        # respuesta directa con tokens
                        return {"access_token": data.get('access_token'), "refresh_token": data.get('refresh_token')}
                    else:
                        # intentar buscar session dentro de data.values
                        for v in data.values():
                            if isinstance(v, dict) and 'access_token' in v:
                                session = v
                                break

            # 2) Si la respuesta es un objeto con atributos
            if session is None:
                # intentar atributos comunes
                session = getattr(user, 'session', None) or getattr(user, 'data', None)
                # si data es dict comprobar session dentro
                if isinstance(session, dict) and 'session' in session and session['session']:
                    session = session['session']

            # 3) Extraer tokens desde session si está presente
            access = None
            refresh = None
            if session:
                if isinstance(session, dict):
                    access = session.get('access_token') or session.get('accessToken')
                    refresh = session.get('refresh_token') or session.get('refreshToken')
                else:
                    access = getattr(session, 'access_token', None) or getattr(session, 'accessToken', None)
                    refresh = getattr(session, 'refresh_token', None) or getattr(session, 'refreshToken', None)

            # 4) Si no hay session, revisar si user tiene data con keys directas
            if not access:
                data = getattr(user, 'data', None) if not isinstance(user, dict) else user.get('data')
                if isinstance(data, dict):
                    access = data.get('access_token') or data.get('accessToken')
                    refresh = data.get('refresh_token') or data.get('refreshToken')

            # 5) Si encontramos access, devolverlo
            if access:
                return {"access_token": access, "refresh_token": refresh}

            # Si llegamos aquí, no encontramos access token. Loggear info segura para depuración.
            try:
                if isinstance(user, dict):
                    logger.debug("Supabase sign_in response is dict with keys: %s", list(user.keys()))
                    if isinstance(user.get('data'), dict):
                        logger.debug("Supabase sign_in data keys: %s", list(user.get('data').keys()))
                else:
                    attrs = [a for a in dir(user) if not a.startswith('_')]
                    logger.debug("Supabase sign_in response type=%s attrs_sample=%s", type(user), attrs[:50])
            except Exception:
                logger.debug("No se pudo inspeccionar respuesta de sign_in_with_password")

            raise InvalidCredentialsError()
        except AuthApiError as e:
            msg = str(e).lower()
            if "email not confirmed" in msg or "not confirmed" in msg or "confirm" in msg:
                raise EmailNotConfirmedError()
            raise InvalidCredentialsError()
        except Exception as e:
            logger.debug("Excepción genérica en sign_in_with_password: %s", repr(e))
            raise InvalidCredentialsError()

    def refresh_with_refresh_token(self, refresh_token: str) -> dict:
        """Usa el endpoint de Supabase Gotrue para renovar tokens a partir de un refresh_token.

        Devuelve dict con access_token y (posiblemente) refresh_token.
        """
        try:
            url = settings.supabase_url.rstrip('/') + '/auth/v1/token?grant_type=refresh_token'
            headers = {
                'apikey': settings.supabase_key,
                'Content-Type': 'application/json'
            }
            payload = {"refresh_token": refresh_token}
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload, headers=headers)
            # Loggear el status y claves de respuesta (no valores)
            try:
                j = resp.json()
                if isinstance(j, dict):
                    logger.debug("Refresh token response status=%s keys=%s", resp.status_code, list(j.keys()))
                else:
                    logger.debug("Refresh token response status=%s type=%s", resp.status_code, type(j))
            except Exception:
                logger.debug("Refresh token response status=%s (no json)", resp.status_code)

            if resp.status_code != 200:
                # Propagar como error de credenciales inválidas
                raise InvalidCredentialsError()
            j = resp.json()
            access = j.get('access_token') or j.get('accessToken')
            refresh = j.get('refresh_token') or j.get('refreshToken')
            return {"access_token": access, "refresh_token": refresh}
        except InvalidCredentialsError:
            raise
        except Exception as e:
            logger.debug("Excepción genérica en refresh_with_refresh_token: %s", repr(e))
            # No exponer detalles
            raise InvalidCredentialsError()

    def create_account(self, email: str, password: str) -> Optional[User]:
        """Crear cuenta usando Supabase. Traduce errores a UserAlreadyExistsError cuando aplique.

        Nota: No logueamos la contraseña ni datos sensibles.
        """
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            # response puede tener .user según la librería
            user = getattr(response, 'user', None)
            if user:
                return User(id=user.id, email=user.email)
            # Si la respuesta no contiene usuario, devolvemos None
            return None
        except AuthApiError as e:
            msg = str(e).lower()
            # Mensaje común cuando el email ya existe
            if "already registered" in msg or "email already registered" in msg or "user already exists" in msg or "duplicate" in msg:
                raise UserAlreadyExistsError(email=email)
            # Otros errores los propagamos como genéricos
            raise
        except Exception:
            # No exponer detalles sensibles
            raise

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