import os
import sys
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="MyApp with fastapi_mcp")
mcp = FastApiMCP(app)

# シンプルなヘルスチェック / ルート
@app.get("/")
async def root() -> dict:
    return {"message": "Hello from FastAPI app (main.py)"}

@app.get("/health", summary="health check")
async def health() -> dict:
    return {"status": "ok"}

