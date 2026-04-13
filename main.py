from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
from typing import Optional, Dict, Any

app = FastAPI(title="LoteriaStars API v5.0 - Rápida + Histórico")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache forte (10 minutos)
cache = {}
CACHE_DURATION = 600

@app.get("/")
def check_status():
    return {"status": "LoteriaStars API v5.0 - Rápida e Completa", "owner": "Joao"}

# ==================== NOVA ROTA DE HISTÓRICO ====================
@app.get("/historico/{loteria}")
def get_historico(loteria: str, limit: int = 50):
    slug = loteria.lower().strip()
    cache_key = f"hist_{slug}_{limit}"
    
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    sources = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}",
        f"https://api.guidi.dev.br/loteria/{slug}/ultimo"
    ]

    for url in sources:
        try:
            resp = requests.get(url, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    result = [_mapear_json(item, slug) for item in data[:limit]]
                else:
                    result = [_mapear_json(data, slug)]
                
                cache[cache_key] = {'data': result, 'time': time.time()}
                return result
        except:
            continue

    return {"error": "Não foi possível carregar histórico"}

# ==================== ROTA PRINCIPAL (ÚLTIMO + POR CONCURSO) ====================
@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    slug = loteria.lower().strip()
    key = f"res_{slug}_{concurso or 'latest'}"
    
    if key in cache and time.time() - cache[key]['time'] < CACHE_DURATION:
        return cache[key]['data']

    # Busca por concurso específico ou último
    suffix = f"/{concurso}" if concurso else "/latest"
    sources = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}{suffix}",
        f"https://api.guidi.dev.br/loteria/{slug}/{'ultimo' if not concurso else concurso}"
    ]

    for url in sources:
        try:
            resp = requests.get(url, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                result = _mapear_json(data, slug) if not isinstance(data, list) else [_mapear_json(item, slug) for item in data]
                cache[key] = {'data': result, 'time': time.time()}
                return result
        except:
            continue

    return {"error": "Não foi possível obter o resultado"}

def _mapear_json(d: Dict, slug: str) -> Dict:
    """Mapeamento agressivo + localGanhadores + Loteca"""
    dezenas = d.get("dezenas") or d.get("listaDezenas") or d.get("numeros") or []
    if slug == "supersete":
        dezenas = [str(x) for x in dezenas]

    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or "",
        "listaDezenas": dezenas,
        "listaDezenas2": d.get("dezenas2") or d.get("listaDezenas2") or [],
        "trevos": d.get("trevos") or d.get("trevo") or [],
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "mesSorte": d.get("mesSorte") or d.get("nomeMesSorte"),
        "acumulou": d.get("acumulou") or d.get("acumulado") or False,
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoProximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or [],
        # Local de ganhadores (várias chaves possíveis)
        "localGanhadores": d.get("localGanhadores") or 
                          d.get("listaMunicipioUfGanhadores") or 
                          d.get("ganhadoresPorLocal") or 
                          d.get("ganhadores") or [],
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }

# ==================== LISTA DE LOTERIAS ====================
@app.get("/loterias")
def listar_loterias():
    return {
        "loterias": [
            "megasena", "lotofacil", "quina", "lotomania",
            "timemania", "duplasena", "diadesorte",
            "maismilionaria", "supersete", "loteca"
        ]
    }
