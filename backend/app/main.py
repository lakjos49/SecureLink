

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import connect_db, close_db
from app.routers import url_router, redirect_router, qr_router, analytics_router, report_router

app = FastAPI(
    title="SecureLink API",
    description=(
        "A secure URL shortening service with risk analysis, QR code generation, "
        "click analytics, and abuse reporting."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

                                                                                
                                                                       
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

                                                                                
@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


                                                                                
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns 200 when the service is up and connected."""
    return {"status": "healthy"}


                                                                                
app.include_router(url_router.router)
app.include_router(redirect_router.router)
app.include_router(qr_router.router)
app.include_router(analytics_router.router)
app.include_router(report_router.router)