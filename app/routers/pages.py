from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.auth import get_optional_user
from app.models.user import User, UserType

router = APIRouter(tags=["Páginas"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        if user.tipo == UserType.ADMIN:
            return RedirectResponse(url="/admin/dashboard", status_code=302)
        return RedirectResponse(url="/client/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})



@router.get("/client/dashboard", response_class=HTMLResponse)
def client_dashboard(request: Request):
    return templates.TemplateResponse("client/dashboard.html", {"request": request})


@router.get("/client/new-appointment", response_class=HTMLResponse)
def client_new_appointment(request: Request):
    return templates.TemplateResponse("client/new_appointment.html", {"request": request})


@router.get("/client/my-appointments", response_class=HTMLResponse)
def client_my_appointments(request: Request):
    return templates.TemplateResponse("client/my_appointments.html", {"request": request})


@router.get("/client/edit-appointment/{appointment_id}", response_class=HTMLResponse)
def client_edit_appointment(request: Request, appointment_id: int):
    return templates.TemplateResponse(
        "client/edit_appointment.html",
        {"request": request, "appointment_id": appointment_id},
    )



@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})


@router.get("/admin/calendar", response_class=HTMLResponse)
def admin_calendar(request: Request):
    return templates.TemplateResponse("admin/calendar.html", {"request": request})


@router.get("/admin/appointments", response_class=HTMLResponse)
def admin_appointments(request: Request):
    return templates.TemplateResponse("admin/appointments.html", {"request": request})


@router.get("/admin/clients", response_class=HTMLResponse)
def admin_clients(request: Request):
    return templates.TemplateResponse("admin/clients.html", {"request": request})


@router.get("/admin/services", response_class=HTMLResponse)
def admin_services(request: Request):
    return templates.TemplateResponse("admin/services.html", {"request": request})


@router.get("/admin/settings", response_class=HTMLResponse)
def admin_settings(request: Request):
    return templates.TemplateResponse("admin/settings.html", {"request": request})
