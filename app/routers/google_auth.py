import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.database.connection import get_db
from app.models.user import User, UserType
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.schemas.user import TokenResponse

router = APIRouter(prefix="/api/auth/google", tags=["Autenticação Google"])

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES_BASIC = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

SCOPES_CALENDAR = SCOPES_BASIC + [
    "https://www.googleapis.com/auth/calendar.events"
]

def get_client_secrets_file():
    return os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secret_470545988882-8ld9hjhlsg5qck0oa3rlam793rd8pt1t.apps.googleusercontent.com.json")

def get_redirect_uri():
    return os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

@router.get("/login")
def google_login(role: str = "CLIENT"):
    client_secrets_file = get_client_secrets_file()
    if not os.path.exists(client_secrets_file):
        raise HTTPException(status_code=500, detail="Arquivo de credenciais do Google não encontrado.")

    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES_BASIC,
        redirect_uri=get_redirect_uri()
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='false',
        prompt='select_account',
        state=role
    )
    
    response = RedirectResponse(authorization_url)
    if hasattr(flow, 'code_verifier'):
        response.set_cookie(key="code_verifier", value=flow.code_verifier, httponly=True, max_age=300)
        
    return response

@router.get("/connect-calendar")
def connect_calendar(request: Request):
    client_secrets_file = get_client_secrets_file()
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES_CALENDAR,
        redirect_uri=get_redirect_uri()
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=request.query_params.get("state", "CONNECT_CALENDAR")
    )
    
    response = RedirectResponse(authorization_url)
    if hasattr(flow, 'code_verifier'):
        response.set_cookie(key="code_verifier", value=flow.code_verifier, httponly=True, max_age=300)
    return response

@router.get("/callback")
def google_callback(request: Request, state: str, code: str, db: Session = Depends(get_db)):
    client_secrets_file = get_client_secrets_file()
    
    is_calendar_flow = state.startswith("CONNECT_CALENDAR") or state == "CLIENT_APPOINTMENT"
    scopes_to_use = SCOPES_CALENDAR if is_calendar_flow else SCOPES_BASIC

    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes_to_use,
        redirect_uri=get_redirect_uri()
    )
    
    code_verifier = request.cookies.get("code_verifier")
    if code_verifier:
        flow.code_verifier = code_verifier
    
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    request_session = google_requests.Request()
    id_info = id_token.verify_oauth2_token(
        credentials.id_token, request_session, flow.client_config["client_id"]
    )

    google_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name")
    
    auth_service = AuthService(db)
    
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
    
    role_requested = UserType.ADMIN if state == "ADMIN" else UserType.CLIENT

    if user:
        user.google_id = google_id
        user.google_access_token = credentials.token
        if credentials.refresh_token:
            user.google_refresh_token = credentials.refresh_token
        user.google_token_expiry = credentials.expiry
        db.commit()
    else:
        user = User(
            nome=name,
            email=email,
            senha_hash="$2b$12$ThisIsAFakeHashForGoogleUsersDoNotUseItDirectlyXXX",
            tipo=role_requested,
            ativo=True,
            google_id=google_id,
            google_access_token=credentials.token,
            google_refresh_token=credentials.refresh_token,
            google_token_expiry=credentials.expiry
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        if role_requested == UserType.CLIENT:
            from app.models.client import Client
            new_client = Client(user_id=user.id)
            db.add(new_client)
            db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "tipo": user.tipo.value}
    )
    
    html_content = f"""
    <html>
    <body>
        <script>
            localStorage.setItem('access_token', '{access_token}');
            localStorage.setItem('user', JSON.stringify({{
                id: {user.id},
                nome: '{user.nome}',
                email: '{user.email}',
                tipo: '{user.tipo.value}'
            }}));
            document.cookie = 'access_token={access_token}; path=/; max-age=3600';
            
            const state = "{state}";
            const isConnect = state.startsWith("CONNECT_CALENDAR");
            const isAppt = state === "CLIENT_APPOINTMENT";

            if (isAppt) {{
                window.location.href = "/client/new-appointment";
            }} else if (isConnect) {{
                window.location.href = '{ "/admin/settings" if user.tipo == UserType.ADMIN else "/client/dashboard" }';
            }} else {{
                window.location.href = '{ "/admin/dashboard" if user.tipo == UserType.ADMIN else "/client/dashboard" }';
            }}
        </script>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")
