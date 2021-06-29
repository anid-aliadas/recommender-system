FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# Copiar archivos a imagen de docker
COPY requirements.txt /app/requirements.txt
COPY ./.env /app/.env

# Archivos de paquete "app"

COPY ./app /app/app

# Instalar dependencias

RUN pip install -r requirements.txt
RUN python -m spacy download es_dep_news_trf