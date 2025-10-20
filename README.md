# Reportes API 🤖📄

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Este proyecto es una **API auxiliar** para la generación de reportes utilizando Inteligencia Artificial. Está diseñada para integrarse y complementar el sistema principal [reportes-ss-generator](https://github.com/Mik318/reportes-ss-generator). Su objetivo es recibir solicitudes, procesarlas utilizando flujos de IA con **Google GenAI**, y devolver los resultados en el formato requerido.

## Propósito Principal

-   **Generación de Reportes con IA:** Recibe peticiones desde el sistema principal y utiliza modelos de IA para generar el contenido de los reportes.
-   **Separación de Responsabilidades:** Mantiene la lógica de negocio del sistema principal desacoplada de la complejidad de la IA, permitiendo que cada parte escale y se mantenga de forma independiente.
-   **Integración Sencilla:** Expone una API RESTful bien definida y segura para la interacción con otros sistemas o microservicios.

***

## Tecnologías Utilizadas

Este proyecto está construido con un stack moderno de Python, enfocado en el rendimiento, la calidad del código y las últimas tecnologías de IA.

| Área | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Core API** | [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/) | Framework web de alto rendimiento para construir APIs rápidas. |
| **IA & Genkit** | [Genkit](https://github.com/genkit-ai/genkit) + [Google GenAI Plugin](https://github.com/genkit-ai/genkit-plugin-google-genai) | Framework para construir flujos de IA robustos y productivos. |
| **Base de Datos**| [Supabase](https://supabase.com/) | Backend-as-a-Service para la gestión de usuarios y datos. |
| **Validación** | [Pydantic](https://docs.pydantic.dev/) | Modelado y validación estricta de datos para la API. |
| **Calidad de Código**| [Ruff](https://github.com/astral-sh/ruff) + [mypy](http://mypy-lang.org/) | Linter y formateador ultrarrápido y chequeo estático de tipos. |
| **Entorno** | [python-dotenv](https://github.com/theskumar/python-dotenv) | Gestión de variables de entorno de forma segura. |

***

## Cómo Empezar

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### **Prerrequisitos**

-   Python 3.9 o superior.
-   Una cuenta de Supabase para la base de datos y autenticación.
-   Credenciales de API para Google GenAI.

### **Instalación**

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/Mik318/reportes-api.git](https://github.com/Mik318/reportes-api.git)
    cd reportes-api
    ```

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura las variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto y añade tus credenciales. Puedes usar el archivo `.env.example` como plantilla.
    ```env
    SUPABASE_URL="TU_URL_DE_SUPABASE"
    SUPABASE_KEY="TU_API_KEY_DE_SUPABASE"
    GOOGLE_API_KEY="TU_API_KEY_DE_GOOGLE_GENAI"
    JWT_SECRET="UN_SECRETO_MUY_SEGURO_PARA_JWT"
    ```

5.  **Ejecuta el servidor de desarrollo:**
    ```bash
    uvicorn app:app --reload
    ```
    La API estará disponible en `http://127.0.0.1:8000`.

***

## Autenticación

La API utiliza autenticación basada en **Tokens JWT (Bearer Token)**. Para acceder a los endpoints protegidos, primero debes obtener un token.

1.  **Crear una cuenta:** (Si es necesario)
    ```bash
    POST /auth/create-account?email=user@example.com&password=securepassword123
    ```

2.  **Obtener un token:**
    Envía tus credenciales al endpoint `/auth/get-token` para recibir un `access_token`.
    ```http
    POST /auth/get-token
    Content-Type: application/json

    {
      "email": "user@example.com",
      "password": "securepassword123"
    }
    ```

3.  **Usar el token:**
    Incluye el token en la cabecera `Authorization` de todas las solicitudes a endpoints protegidos.
    ```http
    Authorization: Bearer <tu_access_token>
    ```

***

## 🔌 Endpoints de la API

A continuación se describen los endpoints disponibles.

### Autenticación

-   `POST /auth/create-account`
    -   **Descripción:** Crea un nuevo usuario en el sistema.
    -   **Parámetros (Query):** `email`, `password`.

-   `POST /auth/get-token`
    -   **Descripción:** Autentica a un usuario y devuelve un token JWT.
    -   **Cuerpo (Body):** `LoginRequest` (`email`, `password`).
    -   **Respuesta:** `AuthTokenResponse` (`access_token`, `token_type`).

### Reportes

-   `POST /reports/`
    -   **Descripción:** Endpoint principal para generar un reporte. **Requiere autenticación**.
    -   **Cuerpo (Body):** `ReportRequest` (`prompt`: Texto o instrucciones para la IA).
    -   **Respuesta:** `ReportResponse` (`report`: Contenido del reporte generado).
    -   **Ejemplo de uso (cURL):**
        ```bash
        curl -X POST "[http://127.0.0.1:8000/reports/](http://127.0.0.1:8000/reports/)" \
        -H "Authorization: Bearer <tu_access_token>" \
        -H "Content-Type: application/json" \
        -d '{
          "prompt": "Genera un reporte de ventas del último trimestre enfocado en la región norte."
        }'
        ```

### Documentación

-   `GET /openapi.yaml`
    -   **Descripción:** Descarga la especificación completa de la API en formato OpenAPI (YAML).

***

## Cómo Contribuir

¡Las contribuciones son siempre bienvenidas! Si tienes sugerencias, mejoras o quieres añadir nuevas funcionalidades, por favor:

1.  Crea un **Fork** del repositorio.
2.  Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3.  Realiza tus cambios y haz **commit** (`git commit -m 'Añade nueva funcionalidad'`).
4.  Haz **push** a tu rama (`git push origin feature/nueva-funcionalidad`).
5.  Abre un **Pull Request**.

También puedes abrir un [issue](https://github.com/Mik318/reportes-api/issues) para reportar bugs o proponer ideas.

## Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Consulta el archivo `LICENSE` para más detalles.
