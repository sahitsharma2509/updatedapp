from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Get the token from the query string
        query_string = parse_qs(scope["query_string"].decode("utf8"))
        token = query_string.get("token")

        if not token:
            # If the token was not provided, just call the inner application
            return await super().__call__(scope, receive, send)

        # Try to authenticate the user
        try:
            # Validate the token
            token_obj = AccessToken(token[0])
            # Get the user
            user = await self.get_user(token_obj["user_id"])
        except Exception as e:
            # If an error occurs, just call the inner application without setting the user
            return await super().__call__(scope, receive, send)

        # Set the user in the scope
        scope["user"] = user

        # Call the inner application
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
