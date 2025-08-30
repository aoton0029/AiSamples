from fastapi import FastAPI
from app.api.routes import router as api_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initialize services or perform startup tasks here
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup tasks can be performed here
    pass

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)