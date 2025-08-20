from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        
        if not token:
            return None
        
        try:
            validated_token = self.get_validated_token(token)
        except AuthenticationFailed as e:
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        try:
            return self.get_user(validated_token), validated_token
        except Exception as e:
            raise AuthenticationFailed(f"Failed to get user: {str(e)}")