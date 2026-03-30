from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any
import time

app = FastAPI(title="SmartLotto API v3.3 - Mais Robusta")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = {}
CACHE_DURATION = 180  # 3 minutos

@app.get("/")
def check_status():
    return {"status": "SmartLotto API v3.3 - Robusta", "owner": "Joao"}

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, tipo: str = "ultimo", concurso: Optional[int] = None):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    cache_key = f"{slug}_{tipo}_{concurso or 'ultimo'}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    sources = [
        ("guidi", f"https://api.guidi.dev.br/loteria/{slug}/ultimo"),
        ("caixa", f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest"),
    ]

    for source_name, url in sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                mapped = _mapear_json_completo(data) if not isinstance(data, list) else [_mapear_json_completo(d) for d in data[-80:]]
                
                cache[cache_key] = {'data': mapped, 'time': time.time()}
                return mapped
        except Exception as e:
            print(f"[{source_name}] Falhou para {slug}: {e}")
            continue

    return {"error": f"Não foi possível obter resultado para {loteria}. Ambas fontes falharam."}


def _mapear_json_completo(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "concurso": d.get("concurso"),
        "dataApuracao": d.get("data") or d.get("dataApuracao"),
        "listaDezenas": d.get("dezenas") or d.get("listaDezenas") or [],
        "listaDezenas2": d.get("dezenas2") or [],
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "localGanhadores": d.get("localGanhadores") or d.get("cidades") or [],
        "listaRateio": d.get("premiacoes") or d.get("listaRateio") or [],
        "acumulou": d.get("acumulou", False),
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }
