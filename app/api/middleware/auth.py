from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED
from jose import jwt, JWTError
import json
from app.config import settings


class JWTMiddleware(BaseHTTPMiddleware):
    """JWT Authentication Middleware."""
    
    # Routes that don't require authentication
    EXEMPT_ROUTES = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for exempt routes
        if any(request.url.path.startswith(route) for route in self.EXEMPT_ROUTES):
            return await call_next(request)
        
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return self._unauthorized_response()
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        try:
            # Verify token
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username = payload.get("sub")
            
            if not username:
                return self._unauthorized_response()
            
            # Add user info to request state
            request.state.username = username
            
        except JWTError:
            return self._unauthorized_response()
        
        response = await call_next(request)
        return response
    
    def _unauthorized_response(self):
        """Return unauthorized response."""
        return Response(
            content=json.dumps({"detail": "Not authenticated"}),
            status_code=HTTP_401_UNAUTHORIZED,
            media_type="application/json"
        )
