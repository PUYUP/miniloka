from urllib.parse import parse_qs

from django.db import close_old_connections
from django.contrib.auth import get_user_model

from channels.db import database_sync_to_async
from channels.auth import AuthMiddlewareStack

User = get_user_model()


@database_sync_to_async
def get_user(token):
    user = User.objects.get(uuid=token)

    if user:
        return user
    return None


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    """
    Yeah, this is black magic:
    https://github.com/django/channels/issues/1399
    """
    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        query_param = parse_qs(self.scope['query_string'])

        # close old connection
        close_old_connections()

        # check JWT token
        # then authenticated user
        # :token set in request param
        if b'token' in query_param:
            token = query_param[b'token'][0].decode('utf-8')
            if token:
                self.scope['user'] = await get_user(token)

        return await self.inner(self.scope, receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))
