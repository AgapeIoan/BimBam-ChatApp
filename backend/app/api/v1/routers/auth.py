from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.config import Config as StarletteConfig

from app.api.v1.deps import get_current_user, get_user_service
from app.core.config import get_settings
from app.db.session import get_async_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.utils.jwt_utils import create_access_token

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

starlette_config = StarletteConfig(environ = {
    "GOOGLE_CLIENT_ID": settings.AUTH.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.AUTH.GOOGLE_CLIENT_SECRET,
    })

oauth = OAuth(starlette_config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

def _parse_frontend_origins() -> list[str]:
    origins = [
        origin.strip()
        for origin in str(settings.AUTH.FRONTEND_ORIGIN).split(",")
        if origin.strip()
    ]
    return origins or [settings.AUTH.FRONTEND_ORIGIN]

def set_auth_cookies_and_redirect(request: Request, user_id: str) -> RedirectResponse:
    token = create_access_token(data={"sub": user_id})
    frontend_origins = _parse_frontend_origins()
    redirect_target = frontend_origins[0]

    # Detect scheme from reverse proxy if present, otherwise from the request.
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    scheme = forwarded_proto or request.url.scheme

    # Determine host used for cookie attributes based on redirect target to avoid
    # misclassifying prod as local when behind proxy.
    redirect_host = redirect_target.split("://")[-1].split("/")[0].split(":")[0].lower()
    is_local_host = redirect_host in {"localhost", "127.0.0.1", "0.0.0.0"}

    # For cross-site usage we need SameSite=None and Secure. Browsers block
    # SameSite=None without Secure.
    samesite = "lax" if is_local_host else "none"
    secure = scheme == "https"

    response = RedirectResponse(url=redirect_target, status_code=302)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=60 * 60 * 24,
    )

    return response

@router.get("/google/login")
async def google_login(request: Request, mode: str = Query("login")):
    request.session['auth_mode'] = mode

    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri) #type: ignore

@router.get("/google/callback")
async def google_callback(request: Request, session: AsyncSession = Depends(get_async_session), user_service: UserService = Depends(get_user_service)):
    
    token = await oauth.google.authorize_access_token(request)  # type: ignore
    user_info = token.get("userinfo")
    
    if user_info is None:
        
        return RedirectResponse(
            url=f"{settings.AUTH.FRONTEND_ORIGIN}?auth_error=google_failed",
            status_code=302,
        )

    provider = "google"
    provider_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name") # noqa: F841
    avatar_url = user_info.get("picture")

    mode = request.session.pop("auth_mode", "login")

    repo = UserRepository(session)

    user = await repo.get_by_provider_id(provider, provider_id)

    if mode == "login":
        if not user:
            # redirect back with "no_account" error
            return RedirectResponse(
                url=f"{settings.AUTH.FRONTEND_ORIGIN}?auth_error=no_account",
                status_code=302,
            )
    else:
        # Signup: create user if missing and force username prompt (empty username)
        if not user:
            user = await user_service.login_or_register(
                provider=provider,
                provider_id=provider_id,
                email=email,
                username="",
                avatar_url=avatar_url,
            )

    return set_auth_cookies_and_redirect(request, str(user.id)) #type: ignore

@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
        "name": current_user.username,
    }

@router.post("/logout")
async def logout():
    response = JSONResponse({"detail": "Logged out"})
    response.delete_cookie("access_token")
    return response
