from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.routers import auth, documents,chat,pages 
from fastapi.staticfiles import StaticFiles
app = FastAPI(title="AI Document Assistant", version="0.1.0")

# Jinja2 templates ka setup — HTML pages serve karne ke liye
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Auth aur Documents routes ko app mein "mount" karna
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(pages.router)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html")

@app.get("/health")
def health_check():
    """Simple endpoint to verify the server aur DB connection zinda hain."""
    return {"status": "ok"}