#!/usr/bin/env python3
"""Script de depuración: prueba sign_in_with_password de Supabase y muestra estructura segura.

USO:
  SUPABASE_URL=... SUPABASE_KEY=... python scripts/debug_supabase_signin.py email@example.com password123

No imprime tokens ni contraseñas; solo muestra la forma de la respuesta para adaptar el parseo.
"""
import os
import sys
import json
from supabase import create_client


def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/debug_supabase_signin.py <email> <password>")
        sys.exit(2)

    email = sys.argv[1]
    password = sys.argv[2]

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Define SUPABASE_URL y SUPABASE_KEY en el entorno antes de ejecutar.")
        sys.exit(2)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        print("Exception al llamar sign_in_with_password:", repr(e))
        sys.exit(1)

    print('--- Tipo de respuesta:', type(resp))

    # Si es dict-like
    if isinstance(resp, dict):
        print('keys:', list(resp.keys()))
        if 'data' in resp and isinstance(resp['data'], dict):
            print('data.keys():', list(resp['data'].keys()))
            # Mostrar claves internas si existen
            for k, v in resp['data'].items():
                print(f"  data[{k}]: type={type(v)}")
    else:
        # Intentar acceder a atributos comunes sin imprimir valores sensibles
        attrs = [a for a in dir(resp) if not a.startswith('_')]
        print('attrs sample:', attrs[:80])
        # intentar extraer .data o .session si existen y mostrar sus claves
        data = getattr(resp, 'data', None)
        session = getattr(resp, 'session', None)
        if isinstance(data, dict):
            print('resp.data.keys():', list(data.keys()))
        else:
            print('resp.data type:', type(data))
        if isinstance(session, dict):
            print('resp.session.keys():', list(session.keys()))
        else:
            print('resp.session type:', type(session))

    print('\n--- Fin de inspección — NO se imprimieron tokens ni contraseñas')


if __name__ == '__main__':
    main()

