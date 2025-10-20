# domain/errors.py

class DomainError(Exception):
    """Clase base para errores de dominio."""
    pass

class UserAlreadyExistsError(DomainError):
    """Lanzado cuando se intenta registrar un email que ya existe."""
    def __init__(self, email: str):
        super().__init__(f"El usuario con el email '{email}' ya existe.")

class InvalidCredentialsError(DomainError):
    """Lanzado cuando las credenciales de inicio de sesión son incorrectas."""
    def __init__(self):
        super().__init__("Las credenciales proporcionadas son inválidas.")

class EmailNotConfirmedError(DomainError):
    """Lanzado cuando el email del usuario no ha sido confirmado en el proveedor de auth."""
    def __init__(self):
        super().__init__("El email del usuario no ha sido confirmado.")
