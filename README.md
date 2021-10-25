# Aliadas recommender system

## Ejecución de proyecto

Asumiendo que se tiene instalado python (versión 3.6 o mayor), para ejecutar el proyecto
se debe de hacer los siguientes pasos

```
# Configurar variables de entorno y crear .env
- Linux y derivados
  $ cp .env.example .env

- Windows
  $ copy .env.example .env

# Instalar paquetes utilizados por el proyecto
  $ pip install -r requirements.txt

# Correr scripts para actualizar los modelos
  $ python update_products_script.py
  ...
  $ python update_recommender_script.py

# Correr aplicación (por defecto escucha en puerto 8000)
  $ uvicorn app.main:app --reload
```

después de correr el último comando, debería devolver esto por consola

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [6811] using watchgod
INFO:     Started server process [6813]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Con las configuraciones añadidas por defecto, se puede correr en docker, lo cual se explicará a continuación.
### Docker

Para correr en docker el proyecto se necesita construir la imagen y ejecutar el contenedor

```
# Desde la raiz del proyecto ejecutar las siguientes lineas de comando

$ docker build -f Dockerfile . -t [nombre_imagen]
$ docker run -d -p [puerto_salida]:80 --name [nombre_contenedor] [nombre_imagen]
```

donde:

- nombre_imagen: es el nombre de la imagen que se desea usar.
- puerto_salida: es el puerto por el cual se desea que escuche la aplicación en el host
  (ejemplo, con puerto_salida = 8000 en localhost, las queries se deben realizar a http://localhost:8000).
  
- nombre_contenedor: es el nombre del contenedor que se desea usar.

### Docker-compose
¡Próximamente!

### Keycloak

El proyecto valida los tokens de keycloak obtenidos por el header de autorización 
usual (por bearer token).

Sin embargo para configurar su uso se deben añadir unas variables de entorno a la aplicación.

El formato se encuentra en .env.example, las variables de entorno a observar son:

- OIDC_CLIENT_ID: id de cliente de aplicación a levantar (consultar credenciales a adminstrador).
- OIDC_CLIENT_SECRET clave secreta de aplicación a levantar (consultar credenciales a adminstrador).
- OIDC_ISSUER: url de aplicación levantada de keycloak (debería ser https://keycloak.aliad.as/auth/)
- OIDC_REALM: realm asociada a aplicación (debería ser "aliadas")

Notar que si se desea solo probar las rutas sin token de autorización, solo debes poner
en la variable de entorno APP_ENVIRONMENT=development, en el caso contrario, hay que poner
production.

## Documentación de las rutas definidas

La documentación se genera automáticamente con el estándar OpenAPI 3.0.

production_host = https://kong.aliad.as/recommender-system
local_host = http://localhost:8000

Esta se puede encontrar en [host]/docs

### Descripción de las rutas

#### Diversified products search: [host]/searcher/products

- __Parametros__: { 'search_text': __query__ }
- __Descripción__: Devuelve los top_n ids de __productos__ que coincidan con la __query__ de búsqueda ingresada. Los ids de productos devueltos por la búsqueda estan reordenados según el algoritmo SOG adaptado para Aliadas.
- __Formato respuesta__: {  
&nbsp;&nbsp;&nbsp;&nbsp; 'results_ids': __array[products_ids]__,  
&nbsp;&nbsp;&nbsp;&nbsp; 'historical': __bool(is_historical)__, # If the data was retrieved from a past query (SOG didn't run)  
&nbsp;&nbsp;&nbsp;&nbsp; 'error': __bool(false)__ || __string(error)__ # False if no error, else returns an error description  
}

#### Products recommender: [host]/recommender/products

- __Parametros__: { 'user_id': __keycloak_id__ }
- __Descripción__: Devuelve los top_n ids de __productos__ más relevantes para el usuario. Los ids estan reordenados según el algoritmo SOG adaptado para Aliadas.
- __Formato respuesta__: { 'response': __array[ products_ids ]__ }

#### Vendors recommender: [host]/recommender/vendors

- __Parametros__: { 'user_id': __keycloak_id__ }
- __Descripción__: Devuelve los top_n ids de __vendors__ más relevantes para el usuario reordenados según el algoritmo SOG adaptado para Aliadas.
- __Formato respuesta__: { 'response': __array[ vendors_ids ]__ }

## Parámetros globales de los algoritmos

### Elastic Search SOG parameters
- __ES_SOG_REL_PARAM_W__: Peso del parámetro de __relevancia__ del algoritmo ES_SOG.
- __ES_SOG_DIV_PARAM_W__: Peso del parámetro de __diversidad__ del algoritmo ES_SOG.
- __ES_SOG_PROF_UI_PARAM_W__: Peso del parámetro de __disimilaridad user-item__ del algoritmo ES_SOG.
- __ES_SOG_UNPOP_I_PARAM_W__: Peso del parámetro de __impopularidad del item__ del algoritmo ES_SOG.
- __ES_SOG_DIV_VEN_PARAM_W__: Peso del parámetro de __diversidad de vendors__ del algoritmo ES_SOG.

### Collaborative Filtering parameters
- __CF_N_TOP_USERS__: Cantidad de usuarios similares al target user a considerar dentro del algoritmo CF. 
- __CF_N_TOP_ITEMS__: Cantidad de itemes relevantes a devolver en el algoritmo CF.
- __CF_SIMILARITY_AMPLIFICATION__: Valor por el cual amplificar la similaridad entre target user y los usuarios similares.
- __CF_COSINE_SIMILARITY_WEIGHT__: Peso del parámetro de similaridad de coseno a utilizar dentro del algoritmo CF. El peso del parámetro de similaridad de Jaccard corresponde al complemento de este parámetro respecto a 1.

### Recommender SOG parameters
- __RS_SOG_REL_PARAM_W__: Peso del parámetro de __relevancia__ del algoritmo RS_SOG.
- __RS_SOG_DIV_PARAM_W__: Peso del parámetro de __diversidad__ del algoritmo RS_SOG.
- __RS_SOG_PROF_UI_PARAM_W__: Peso del parámetro de __disimilaridad user-item__ del algoritmo RS_SOG.
- __RS_SOG_UNPOP_I_PARAM_W__: Peso del parámetro de __impopularidad del item__ del algoritmo RS_SOG.

### Other parameters

- __TOP_N_VOCAB_WORDS_PERCENTAGE__: Porcentaje del total de palabras del corpus a utilizar como top_n palabras más frecuentes.
- __HISTORICAL_QUERIES_DAYS_AGO__: Días atrás a considerar en el historial de queries para el algoritmo ES_SOG

## Anexos

- Docs de FastAPI: https://fastapi.tiangolo.com/

## Contacto

- Discord: Advent#7908
- Whatsapp: +56982733475

