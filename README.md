# EDULAB Backend

## Requisitos

* Python 3.12+
* PostgreSQL 18+
* Git

## Instalación

```bash
git clone <repo>
cd edulab-backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## Configuración

Crear archivo `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:TU_PASSWORD@localhost:5432/edulab
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
DEV_MODE=True
MOCK_FIREBASE_AUTH=False
```

Copiar:

```txt
firebase-credentials.json
```

en la raíz del proyecto.

## Base de datos

Crear:

```sql
CREATE DATABASE edulab;
```

Luego ejecutar:

```bash
python reset_db.py
```

## Ejecutar

```bash
uvicorn app.main:app --reload
```

Backend:

```txt
http://127.0.0.1:8000
```

Swagger:

```txt
http://127.0.0.1:8000/docs
```
