from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Permite que o seu app Flutter acesse o servidor sem bloqueios de segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://loterias.caixa.gov.br/"
}

@app.get("/")
def home():
    return {"status": "SmartLotto API Online"}

@app.get("/resultado/{modalidade}")
def get_resultado(modalidade: str):
    # O servidor vai buscar na Caixa por você
    url = f"https://servicebus2.caixa.gov.br/portalloterias/api/{modalidade}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
