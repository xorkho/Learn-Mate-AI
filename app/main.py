from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.routers import auth, documents

app = FastAPI(title="AI Document Assistant", version="0.1.0")

# Jinja2 templates ka setup — HTML pages serve karne ke liye
templates = Jinja2Templates(directory="app/templates")

# Auth aur Documents routes ko app mein "mount" karna
app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/dashboard")
def dashboard(request: Request):
    """
    HTML page return karta hai. Note: ye route khud protected NAHI hai
    (server-side check nahi karta login hai ya nahi) — actual security
    JavaScript se hoga: agar localStorage mein valid token na ho,
    JS khud /login pe redirect kar dega. API calls hamesha token
    ke sath jayengi jo backend verify karega.
    """
    return templates.TemplateResponse(request=request, name="dashboard.html")

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