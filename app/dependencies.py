from starlette.config import Config
from keycloak import KeycloakAdmin

config = Config('.env')

# Seteo de administrador de Keycloak

def obtain_admin_privilege_keycloak():
    keycloak_admin = KeycloakAdmin(server_url=config('OIDC_ISSUER'),
                                   client_id=config('OIDC_CLIENT_ID'),
                                   realm_name=config('OIDC_REALM'),
                                   client_secret_key=config('OIDC_CLIENT_SECRET'),
                                   verify=True)
    return keycloak_admin