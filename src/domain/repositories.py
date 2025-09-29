from abc import ABC, abstractmethod
from typing import Optional
from .models import User

class AuthRepository(ABC):
    @abstractmethod
    def get_user_from_token(self, token: str) -> Optional[User]:
        pass

    @abstractmethod
    def sign_in_with_password(self, email: str, password: str) -> str:
        pass

