from fastapi import HTTPException
import requests
import os

class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")

    def send_request(self, model_name: str, payload: dict):
        url = f"{self.base_url}/models/{model_name}/run"
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise HTTPException(status_code=response.status_code, detail=str(http_err))
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err))

    def list_models(self):
        url = f"{self.base_url}/models"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise HTTPException(status_code=response.status_code, detail=str(http_err))
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err))