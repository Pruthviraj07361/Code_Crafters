from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get('query_string', b'').decode())
        token_key = query.get('token', [None])[0]
        if token_key:
            scope = dict(scope)
            scope['user'] = await self.get_user(token_key)
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token_key):
        try:
            token = Token.objects.select_related('user').get(key=token_key)
        except Token.DoesNotExist:
            return AnonymousUser()
        return token.user if token.user.is_active else AnonymousUser()