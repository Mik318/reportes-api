# Reportes API

Este proyecto es una **API auxiliar** para la generación de reportes con Inteligencia Artificial, diseñada para integrarse y complementar el sistema principal [reportes-ss-generator](https://github.com/Mik318/reportes-ss-generator). Su objetivo es recibir solicitudes de generación de reportes desde el repositorio principal, procesarlas utilizando IA y devolver los resultados en el formato requerido.

## Propósito

- **Auxiliar de reportes:** Recibe peticiones desde [reportes-ss-generator](https://github.com/Mik318/reportes-ss-generator) y genera reportes con IA.
- **Separación de responsabilidades:** Permite escalar y mantener el sistema principal desacoplado de la lógica de IA y generación de reportes.
- **Fácil integración:** Expone endpoints RESTful para la interacción con otros sistemas o microservicios.

## Tecnologías utilizadas

- **Core API:**  
  - [FastAPI](https://fastapi.tiangolo.com/) - Framework para desarrollar APIs rápidas y modernas.
  - [uvicorn[standard]](https://www.uvicorn.org/) - Servidor ASGI recomendado para FastAPI.

- **Validación de datos:**  
  - [Pydantic](https://docs.pydantic.dev/) - Modelado y validación de datos robusta.

- **Inteligencia Artificial / Genkit:**  
  - [Genkit](https://github.com/genkit-ai/genkit) - Framework para flujos de IA.
  - [genkit-plugin-google-genai](https://github.com/genkit-ai/genkit-plugin-google-genai) - Plugin para integrar modelos de Google GenAI.

- **Base de datos / Backend:**  
  - [Supabase](https://supabase.com/) - Backend como servicio y base de datos (cliente Python).

- **Variables de entorno:**  
  - [python-dotenv](https://github.com/theskumar/python-dotenv) - Carga y gestión de variables desde archivos `.env`.

- **Calidad de código / Chequeos estáticos:**  
  - [mypy](http://mypy-lang.org/) - Chequeo estático de tipos en Python.
  - [ruff](https://github.com/astral-sh/ruff) - Linter rápido y formateador.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Mik318/reportes-api.git
   cd reportes-api
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Crea y configura tu archivo `.env` según tus credenciales y configuración de Supabase/GenAI.

4. Ejecuta el servidor de desarrollo:
   ```bash
   uvicorn app:app --reload
   ```

## Uso típico

El sistema [reportes-ss-generator](https://github.com/Mik318/reportes-ss-generator) realiza peticiones HTTP a esta API para solicitar la generación de reportes. La API procesa los datos utilizando IA (Genkit + Google GenAI) y devuelve el reporte generado.

## Ejemplo de endpoint

```http
POST /reportes
Content-Type: application/json

{
  "tipo": "pdf",
  "datos": { ... }
}
```

## Contribuir

¡Las contribuciones son bienvenidas! Puedes abrir issues o pull requests con sugerencias, mejoras o nuevas funcionalidades relacionadas a la generación de reportes con IA.

## Licencia

Este proyecto está bajo la licencia MIT.

---

¿Dudas o sugerencias? Abre un [issue](https://github.com/Mik318/reportes-api/issues).
