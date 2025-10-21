# Reportes API 🤖📄

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Este proyecto es una **API auxiliar** para la generación de reportes utilizando Inteligencia Artificial. Está diseñada para integrarse y complementar el sistema principal [reportes-ss-generator](https://github.com/Mik318/reportes-ss-generator). Su objetivo es recibir solicitudes, procesarlas utilizando flujos de IA con **Google GenAI (Gemini)**, y devolver los resultados en el formato requerido.

## ✨ Características Principales

- **Generación de Reportes con IA**: Utiliza Google Gemini para crear reportes profesionales basados en listas de actividades
- **Autenticación JWT Segura**: Sistema completo de autenticación con tokens Bearer y refresh tokens
- **Arquitectura Limpia**: Implementa DDD (Domain-Driven Design) con separación clara de responsabilidades
- **Base de Datos**: Integración completa con Supabase para gestión de usuarios
- **Alto Rendimiento**: Construida con FastAPI para máxima velocidad y eficiencia
- **CORS Configurado**: Permite integración con frontends web (Angular, React, etc.)

## Propósito Principal

-   **Generación de Reportes con IA:** Recibe listas de actividades y utiliza modelos de IA (Gemini) para generar reportes profesionales en primera persona y tiempo pasado.
-   **Separación de Responsabilidades:** Mantiene la lógica de negocio del sistema principal desacoplada de la complejidad de la IA, permitiendo que cada parte escale y se mantenga de forma independiente.
-   **Integración Sencilla:** Expone una API RESTful bien definida y segura para la interacción con otros sistemas o microservicios.

***

## Tecnologías Utilizadas

Este proyecto está construido con un stack moderno de Python, enfocado en el rendimiento, la calidad del código y las últimas tecnologías de IA.

| Área | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Core API** | [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/) | Framework web de alto rendimiento para construir APIs rápidas. |
| **IA & Genkit** | [Genkit](https://github.com/genkit-ai/genkit) + [Google GenAI Plugin](https://github.com/genkit-ai/genkit-plugin-google-genai) | Framework para construir flujos de IA robustos con Gemini 2.5 Flash. |
| **Base de Datos**| [Supabase](https://supabase.com/) | Backend-as-a-Service para la gestión de usuarios, autenticación y datos. |
| **Validación** | [Pydantic](https://docs.pydantic.dev/) | Modelado y validación estricta de datos para la API. |
| **Calidad de Código**| [Ruff](https://github.com/astral-sh/ruff) + [mypy](http://mypy-lang.org/) | Linter y formateador ultrarrápido y chequeo estático de tipos. |
| **Entorno** | [python-dotenv](https://github.com/theskumar/python-dotenv) | Gestión de variables de entorno de forma segura. |

***

## Cómo Empezar

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### **Prerrequisitos**

-   Python 3.9 o superior.
-   Una cuenta de Supabase para la base de datos y autenticación.
-   Credenciales de API para Google GenAI (Gemini).

### **Instalación**

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/Mik318/reportes-api.git
    cd reportes-api
    ```

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv env
    source env/bin/activate  # En Windows usa `env\Scripts\activate`
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura las variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto y añade tus credenciales:
    ```env
    # Supabase Configuration
    SUPABASE_URL="https://tu-proyecto.supabase.co"
    SUPABASE_KEY="tu_anon_key_de_supabase"
    
    # Google GenAI Configuration
    GEMINI_API_KEY="tu_api_key_de_gemini"
    GEMINI_MODEL="googleai/gemini-2.5-flash"  # Opcional, usa por defecto
    
    # Performance (Opcional)
    GENAI_TIMEOUT="20"  # Timeout para llamadas a IA en segundos
    ```

5.  **Ejecuta el servidor de desarrollo:**
    ```bash
    # Opción 1: Usar uvicorn directamente
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    
    # Opción 2: Desde el directorio src
    cd src && python -m uvicorn main:app --reload
    ```
    La API estará disponible en `http://127.0.0.1:8000`.

6.  **Verifica la instalación:**
    Accede a `http://127.0.0.1:8000/docs` para ver la documentación interactiva (Swagger UI).

***

## Sistema de Autenticación

La API utiliza autenticación basada en **Tokens JWT (Bearer Token)** con soporte para refresh tokens. Todos los endpoints de reportes requieren autenticación.

### Flujo de Autenticación

1. **Crear cuenta** → 2. **Obtener tokens** → 3. **Usar access_token** → 4. **Renovar con refresh_token**

### Seguridad

- Tokens JWT seguros con expiración
- Refresh tokens para renovación automática
- Validación de email (debe confirmarse en Supabase)
- Encriptación de contraseñas
- Headers Authorization Bearer estándar

***

## Endpoints de la API

### Autenticación (`/auth`)

#### **POST** `/auth/create-account`
Crea una nueva cuenta de usuario en el sistema.

**Body (JSON):**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseñaSegura123"
}
```

**Respuesta (201):**
```json
{
  "id": "uuid-del-usuario",
  "email": "usuario@ejemplo.com"
}
```

**Errores:**
- `409` - Usuario ya existe
- `400` - Datos inválidos

---

#### **POST** `/auth/get-token`
Autentica un usuario y devuelve tokens de acceso.

**Body (JSON):**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseñaSegura123"
}
```

**Respuesta (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Errores:**
- `401` - Credenciales inválidas
- `403` - Email no confirmado

---

#### **POST** `/auth/refresh-token`
Renueva el access_token usando un refresh_token válido.

**Body (JSON):**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Respuesta (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Errores:**
- `401` - Refresh token inválido o expirado

---

#### **GET** `/auth/verify-token`
Verifica la validez del token actual y devuelve información del usuario.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Respuesta (200):**
```json
{
  "id": "uuid-del-usuario",
  "email": "usuario@ejemplo.com"
}
```

**Errores:**
- `401` - Token inválido o no proporcionado

---

### Reportes (`/reports`)

#### **POST** `/reports/` 
**Endpoint principal** para generar reportes usando IA. **Requiere autenticación**.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "actividades": [
    "Participé en la reunión de equipo para revisar los objetivos del trimestre",
    "Desarrollé la nueva funcionalidad de autenticación para la aplicación web",
    "Realicé pruebas de integración con el sistema de base de datos",
    "Documenté los procedimientos de despliegue en el wiki del proyecto"
  ]
}
```

**Respuesta (200):**
```json
{
  "report": "Durante la jornada laboral, participé activamente en la reunión de equipo donde revisamos detalladamente los objetivos establecidos para el trimestre actual. Posteriormente, me dediqué al desarrollo de la nueva funcionalidad de autenticación para la aplicación web, implementando las medidas de seguridad necesarias. Continué con la realización de pruebas exhaustivas de integración con el sistema de base de datos, verificando la correcta conectividad y funcionamiento. Finalmente, documenté de manera completa los procedimientos de despliegue en el wiki del proyecto, asegurando que el equipo tenga acceso a información actualizada y detallada para futuras implementaciones."
}
```

**Características del reporte generado:**
-️ **Primera persona y tiempo pasado**
- **Estilo profesional y coherente**
- **Longitud optimizada** (900-1500 caracteres aprox.)
- **Combina y conecta las actividades** de forma natural

**Errores:**
- `401` - Token inválido o no proporcionado
- `400` - Lista de actividades vacía o inválida
- `500` - Error en la generación del reporte

---

### Documentación (`/`)

#### **GET** `/openapi.yaml`
Descarga la especificación completa de la API en formato OpenAPI 3.0 (YAML).

**Respuesta (200):**
- Archivo YAML con toda la especificación de la API
- Headers: `Content-Disposition: attachment; filename="openapi.yaml"`

---

## CORS y Integración Frontend

La API está configurada para permitir requests desde:
- `http://localhost:4200` (Angular dev server)
- `https://mik318.github.io` (GitHub Pages)

Para añadir más dominios, edita el archivo `src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://tu-dominio.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Ejemplos de Uso

### JavaScript/TypeScript (Frontend)

```typescript
// Obtener token
const loginResponse = await fetch('http://localhost:8000/auth/get-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'usuario@ejemplo.com',
    password: 'contraseña123'
  })
});

const { access_token } = await loginResponse.json();

// Generar reporte
const reportResponse = await fetch('http://localhost:8000/reports/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    actividades: [
      'Desarrollé nuevas funcionalidades',
      'Participé en reuniones de equipo',
      'Realicé pruebas de código'
    ]
  })
});

const { report } = await reportResponse.json();
console.log(report);
```

### cURL

```bash
# 1. Obtener token
curl -X POST "http://localhost:8000/auth/get-token" \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@ejemplo.com","password":"contraseña123"}'

# 2. Generar reporte (usar el token obtenido)
curl -X POST "http://localhost:8000/reports/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "actividades": [
      "Desarrollé nuevas funcionalidades para el sistema",
      "Participé en reuniones de planificación del sprint",
      "Realicé pruebas unitarias y de integración"
    ]
  }'
```

### Python (requests)

```python
import requests

# Obtener token
login_response = requests.post(
    'http://localhost:8000/auth/get-token',
    json={
        'email': 'usuario@ejemplo.com',
        'password': 'contraseña123'
    }
)
access_token = login_response.json()['access_token']

# Generar reporte
report_response = requests.post(
    'http://localhost:8000/reports/',
    headers={'Authorization': f'Bearer {access_token}'},
    json={
        'actividades': [
            'Implementé la funcionalidad de reportes automáticos',
            'Optimicé las consultas a la base de datos',
            'Documenté los nuevos endpoints de la API'
        ]
    }
)

reporte = report_response.json()['report']
print(reporte)
```

---

## Arquitectura del Proyecto

```
src/
├── main.py                          # Punto de entrada de FastAPI
├── config.py                        # Configuración global
├── genkit_flow.py                   # Flujo de IA con Genkit/Gemini
├── domain/                          # Capa de dominio (modelos, errores)
│   ├── models.py                   
│   ├── errors.py                   
│   └── repositories.py             
├── application/                     # Capa de aplicación (servicios)
│   └── services.py                 
└── infrastructure/                  # Capa de infraestructura
    └── api/
        ├── dependencies.py          # Dependencias de FastAPI (JWT)
        ├── routers/                # Endpoints organizados
        │   ├── auth.py            
        │   └── reports.py         
        └── repositories/           # Implementaciones de repositorios
            └── supabase_auth_repository.py
```

**Principios aplicados:**
-  **Domain-Driven Design (DDD)**
- **Clean Architecture**
- **Inversión de dependencias**
- **Separación de responsabilidades**

---

##  Variables de Entorno

| Variable | Descripción | Requerido | Ejemplo |
|----------|-------------|-----------|---------|
| `SUPABASE_URL` | URL de tu proyecto Supabase | ✅ | `https://abc123.supabase.co` |
| `SUPABASE_KEY` | Anon key de Supabase | ✅ | `eyJhbGciOiJIUzI1NiIs...` |
| `GEMINI_API_KEY` | API key de Google GenAI | ✅ | `AIzaSyA...` |
| `GEMINI_MODEL` | Modelo de Gemini a usar | ❌ | `googleai/gemini-2.5-flash` |
| `GENAI_TIMEOUT` | Timeout para IA (segundos) | ❌ | `20` |

---

## Manejo de Errores

La API implementa un manejo robusto de errores con fallbacks automáticos:

### Errores de Autenticación
- **401 Unauthorized**: Token inválido, expirado o no proporcionado
- **403 Forbidden**: Email no confirmado en Supabase
- **409 Conflict**: Usuario ya existe al crear cuenta

### Errores de Reportes
- **400 Bad Request**: Lista de actividades inválida o vacía
- **500 Internal Server Error**: Error en IA con fallback a generador local

### Fallback Automático
Si la IA no está disponible o falla, la API automáticamente utiliza un **generador local** que:
- Combina las actividades en un párrafo coherente
- Respeta la longitud máxima de caracteres
- Mantiene el formato profesional
- Evita que la API falle completamente

---

## Rendimiento y Optimizaciones

### Optimizaciones de IA
- **Instrucciones directas**: Elimina complejidad innecesaria
-  **Timeouts configurables**: Evita esperas excesivas
- **Reintentos automáticos**: Con timeout doble en caso de fallo

### Optimizaciones de API
- **FastAPI**: Framework ultrarrápido basado en Starlette
- **Pydantic**: Validación eficiente de datos
- **Async/await**: Programación asíncrona nativa
- **Conexión persistente**: Reutiliza conexiones a Supabase

---

## Desarrollo y Calidad de Código

### Herramientas de Calidad
```bash
# Linting y formateo con Ruff
ruff check src/
ruff format src/

# Verificación de tipos con mypy
mypy src/

# Ejecutar todos los checks
ruff check src/ && ruff format src/ && mypy src/
```

### Scripts de Desarrollo

El directorio `scripts/` incluye herramientas útiles:
- `debug_supabase_signin.py` - Debug de autenticación con Supabase
- `test_genkit_flow_local.py` - Pruebas locales del flujo de IA

---

## Cómo Contribuir

¡Las contribuciones son siempre bienvenidas! Si tienes sugerencias, mejoras o quieres añadir nuevas funcionalidades:

1. **Fork** el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios siguiendo las convenciones del proyecto
4. Ejecuta los tests y verificaciones de calidad
5. Haz commit (`git commit -m 'Añade nueva funcionalidad'`)
6. Push a tu rama (`git push origin feature/nueva-funcionalidad`)
7. Abre un **Pull Request**

### Guidelines de Contribución
- Mantén la arquitectura limpia existente
- Añade tests para nuevas funcionalidades
- Documenta cambios en el README si es necesario
- Sigue las convenciones de código (Ruff + mypy)

También puedes abrir un [issue](https://github.com/Mik318/reportes-api/issues) para reportar bugs o proponer ideas.

---

## 📄 Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Consulta el archivo `LICENSE` para más detalles.

---

## 🤝 Integración con Proyecto Principal

Esta API está diseñada para integrarse perfectamente con [reportes-ss-generator](https://github.com/Mik318/reportes-ss-generator), proporcionando:

- 🔗 **Endpoints compatibles** con el frontend Angular
- 🔐 **Autenticación unificada** via Supabase
- ⚡ **Respuestas optimizadas** para UX fluida
- 📊 **Formato consistente** de reportes
