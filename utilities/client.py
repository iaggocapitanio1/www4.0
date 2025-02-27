from django.conf import settings
from requests_auth import OAuth2ClientCredentials, OAuth2, JsonTokenFileCache

OAuth2.token_cache = JsonTokenFileCache('./cache.json')

oauth = OAuth2ClientCredentials(
    client_id=settings.KEYROCK_CLIENT.get("CLIENT_ID"),
    client_secret=settings.KEYROCK_CLIENT.get("CLIENT_SECRET"),
    token_url=settings.KEYROCK_CLIENT.get("TOKEN_URL"),

)
