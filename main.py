from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# CABEÇALHOS REFORÇADOS (Para evitar o 403)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://loterias.caixa.gov.br/",
    "Origin": "https://loterias.caixa.gov.br",
    "Connection": "keep-alive",
}

@app.get("/")
def home():
    return {"status": "SmartLotto API Online", "v": "1.1"}

@app.get("/resultado/{modalidade}")
def get_resultado(modalidade: str):
    # O slug da caixa às vezes precisa ser minúsculo e sem traço
    slug = modalidade.lower().replace("-", "")
    url = f"https://servicebus2.caixa.gov.br/portalloterias/api/{slug}"
    
    try:
        # Usamos um timeout um pouco maior e os novos HEADERS
        response = requests.get(url, headers=HEADERS, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        
        # Se der erro, retornamos o status para depurar
        return {"error": f"Caixa retornou status {response.status_code}", "url_tentada": url}
        
    except Exception as e:
        return {"error": str(e)}
