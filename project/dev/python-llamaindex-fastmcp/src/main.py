from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from database.connections import get_postgres_session, get_mongodb_session

app = FastAPI()

# Initialize database connections
postgres_engine = create_engine(DATABASE_URL['postgres'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

@app.on_event("startup")
def startup_event():
    # Create database connections or any startup tasks
    pass

@app.on_event("shutdown")
def shutdown_event():
    # Close database connections or any cleanup tasks
    pass

@app.get("/")
def read_root():
    return {"message": "Welcome to the LlamaIndex and FastMCP API"}

# Include additional routes
# from api.routes import health, query
# app.include_router(health.router)
# app.include_router(query.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)