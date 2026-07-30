from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app.routers import auth

app = FastAPI(title="AI Document Assistant", version="0.1.0")

# Jinja2 templates ka setup — HTML pages serve karne ke liye
templates = Jinja2Templates(directory="app/templates")

# Auth routes ko app mein "mount" karna
app.include_router(auth.router)


@app.get("/health")
def health_check():
    """Simple endpoint to verify the server aur DB connection zinda hain."""
    return {"status": "ok"}
