from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/workspace/{document_id}")
def workspace_page(request: Request, document_id: int):
    return templates.TemplateResponse(
        "workspace.html",
        {"request": request, "document_id": document_id},
    )

@router.get("/progress")
def progress_page(request: Request):
    return templates.TemplateResponse("progress.html", {"request": request})