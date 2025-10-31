from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import auth, devices, zones, users, companies

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Greenhouse IoT Platform",
    description="Multi-tenant IoT platform for greenhouse management",
    version="1.0.0"
)

# CORS Configuration - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(zones.router, prefix="/api/zones", tags=["Zones"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])

@app.get("/")
def read_root():
    return {"message": "Greenhouse IoT Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
