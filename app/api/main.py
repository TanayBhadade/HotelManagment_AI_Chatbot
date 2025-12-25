import uvicorn
from fastapi import FastAPI
from app.core.config import settings
from app.db.session import engine, Base

# Import the new routers
from app.api.v1.routers import chat, bookings

# Create Tables (if they don't exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# --- INCLUDE ROUTERS ---
# This connects the separate files to the main app
app.include_router(chat.router, tags=["Chat"])
app.include_router(bookings.router, tags=["Bookings"])

@app.get("/")
def health_check():
    return {"status": "running", "project": settings.PROJECT_NAME}

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8001, reload=True)