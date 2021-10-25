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
local_host = http://127.0.0.1:8000

Esta se puede encontrar en [host]/docs

### Descripción de las rutas

...

## Anexos

- Docs de FastAPI: https://fastapi.tiangolo.com/

## Contacto

- Discord: Advent#7908
- Whatsapp: +56982733475

