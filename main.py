from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, List, Dict, Any
import time

app = FastAPI(title="SmartLotto API v3.2 - Potencializada")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache simples em memória (melhora velocidade)
cache = {}
CACHE_DURATION = 300  # 5 minutos

@app.get("/")
def check_status():
    return {
        "status": "SmartLotto API v3.2 - Potencializada",
        "owner": "Joao",
        "features": ["cache", "fallback", "todas_loterias", "local_ganhadores"]
    }

# Lista completa de loterias suportadas
LOTTERIAS_SUPORTADAS = {
    "megasena", "lotofacil", "quina", "lotomania", "timemania", 
    "duplasena", "diadesorte", "maismilionaria", "supersete", "loteca"
}

@app.get("/resultado/{loteria}")
def get_resultado(
    loteria: str,
    tipo: str = "ultimo",
    concurso: Optional[int] = None
):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    if slug not in LOTTERIAS_SUPORTADAS and slug != "all":
        return {"error": f"Loteria '{loteria}' não suportada. Use: {list(LOTTERIAS_SUPORTADAS)}"}

    # Cache key
    cache_key = f"{slug}_{tipo}_{concurso}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Tenta primeiro a API mais confiável (guidi.dev.br)
    try:
        if concurso:
            url = f"https://api.guidi.dev.br/loteria/{slug}/{concurso}"
        elif tipo.lower() == "historico":
            url = f"https://api.guidi.dev.br/loteria/{slug}"
        else:
            url = f"https://api.guidi.dev.br/loteria/{slug}/ultimo"

        response = requests.get(url, timeout=25)
        if response.statusCode == 200:
            dados = response.json()
            mapped = _mapear_json_completo(dados) if not isinstance(dados, list) else [_mapear_json_completo(d) for d in dados[-100:]]
            
            # Salva no cache
            cache[cache_key] = {'data': mapped, 'time': time.time()}
            return mapped
    except:
        pass  # fallback para a API antiga

    # Fallback para a API antiga (sua anterior)
    try:
        if concurso:
            url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{concurso}"
        elif tipo.lower() == "historico":
            url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
        else:
            url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest"

        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            dados = response.json()
            mapped = _mapear_json_completo(dados) if not isinstance(dados, list) else [_mapear_json_completo(d) for d in dados[-100:]]
            cache[cache_key] = {'data': mapped, 'time': time.time()}
            return mapped
    except Exception as e:
        return {"error": f"Falha em ambas as fontes: {str(e)}"}

    return {"error": "Não foi possível obter o resultado"}

def _mapear_json_completo(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "concurso": d.get("concurso"),
        "dataApuracao": d.get("data") or d.get("dataApuracao"),
        "listaDezenas": d.get("dezenas") or d.get("listaDezenas") or [],
        "listaDezenas2": d.get("dezenas2") or [],  # Dupla Sena
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoPróximoConcurso") or 0),
        "localGanhadores": d.get("localGanhadores") or d.get("cidades") or [],
        "listaRateio": d.get("premiacoes") or d.get("listaRateio") or [],
        "listaTrevos": d.get("trevos") or [],
        "nomeTimeCoracao": d.get("timeCoracao"),
        "nomeMesSorte": d.get("mesSorte"),
        "acumulou": d.get("acumulou", False),
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }

# Endpoint para listar todas as loterias suportadas
@app.get("/loterias")
def listar_loterias():
    return {"loterias": list(LOTTERIAS_SUPORTADAS)}
