# fastapi-service-template

Este repositorio contiene un proyecto vacío de FastAPI pero con las configuraciones recurrentes
que se deben usar en los servicios a desarrollar a futuro.

Además posee un formato de paquetes que permite ordenar el código en middlewares,
modelos y rutas (pueden surgir más paquetes según se vaya revisando lo práctico 
de este formato)

Este se irá actualizando (y refactorizando) en función de los requisitos recurrentes 
que tendrán los servicios a desarrollar.

## Ejemplos de modelos y rutas

Se pueden ver ejemplos de estos en algún proyecto derivado de este repositorio

(Por ejemplo este: https://github.com/anid-aliadas/fastapi-action-logs-service)

Aún asi si surgen dudas, se puede consultar a la documentación del framework
(adjunto en anexos), o a mi (ver sección contacto).

## Configuraciones

El presente proyecto presenta configuraciones para las siguientes tecnologías.

- Docker
- Keycloak

## Ejecución de proyecto

Asumiendo que se tiene instalado python (versión 3.6 o mayor), para ejecutar el proyecto
se debe de hacer los siguientes pasos

```
# Configurar variables de entorno y crear .env
$ cp .env.example .env

# Instalar paquetes utilizados por el proyecto
$ pip install -r requirements.txt

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

Esta se puede encontrar en [dirección_de_host]/docs (asumiendo que la aplicación
está en modo de desarrollo)

## Anexos

- Docs de FastAPI: https://fastapi.tiangolo.com/

## Contacto

- Discord: Advent#7908
- Whatsapp: +56982733475

