from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Isso evita erros de segurança quando o celular tenta falar com o servidor
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
    return {"status": "SmartLotto API Online", "projeto": "Unilab 4 Semestre"}

@app.get("/resultado/{modalidade}")
def get_resultado(modalidade: str):
    # O Python agora busca QUALQUER modalidade que você pedir
    url = f"https://servicebus2.caixa.gov.br/portalloterias/api/{modalidade}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json() # Retorna TUDO (incluindo trevos e times)
        return {"error": f"Caixa retornou status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
