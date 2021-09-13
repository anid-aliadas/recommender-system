from ..dependencies import config
from starlette.middleware.base import BaseHTTPMiddleware
from keycloak import KeycloakOpenID
from jose import JWTError
from fastapi.responses import JSONResponse

'''
Este es el middleware que permite filtrar consultas de usuarios que están deslogeados de Keycloak, verifica
el token y guarda los datos del usuario para las siguientes consultas que se realicen. Estos datos se pueden
obtener con request.state.user_data
'''

keycloak_openid = KeycloakOpenID(server_url=config('OIDC_ISSUER'),
                    client_id=config('OIDC_CLIENT_ID'),
                    realm_name=config('OIDC_REALM'),
                    client_secret_key=config('OIDC_CLIENT_SECRET'))

class ValidateUserToken(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            token = request.headers["Authorization"].split()[1]
            #Token validation
            public_key = (
                "-----BEGIN PUBLIC KEY-----\n"
                + keycloak_openid.public_key()
                + "\n-----END PUBLIC KEY-----"
            )
            options = {"verify_signature": True, "verify_aud": False, "exp": True}
            token_info = keycloak_openid.decode_token(token, key=public_key, options=options)
            request.state.user_data = token_info
            response = await call_next(request)
            return response
        except (JWTError):
            return JSONResponse(
                status_code=401,
                content="Usted no está autorizado para realizar la presente consulta"
            )