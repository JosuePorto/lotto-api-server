from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any
import time

app = FastAPI(title="SmartLotto API v4.5 - Palpite Fácil")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache simples em memória
cache = {}
CACHE_DURATION = 300  # 5 minutos

@app.get("/")
def check_status():
    return {
        "status": "SmartLotto API v4.5 - Palpite Fácil",
        "owner": "Joao",
        "message": "Suporte completo a todas loterias da Caixa + Cache + Fallback"
    }

@app.get("/loterias")
def listar_loterias():
    return {
        "loterias": [
            "megasena", "lotofacil", "quina", "lotomania", "timemania",
            "duplasena", "diadesorte", "maismilionaria", "supersete", "loteca"
        ]
    }

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    cache_key = f"{slug}_{concurso or 'ultimo'}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Fontes em ordem de prioridade
    sources = [
        f"https://api.guidi.dev.br/loteria/{slug}/ultimo",
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest",
    ]

    if concurso:
        sources.insert(0, f"https://api.guidi.dev.br/loteria/{slug}/{concurso}")

    for url in sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    data = data[-1]

                mapped = _mapear_json_agressivo(data, slug)
                cache[cache_key] = {"data": mapped, "time": time.time()}
                return mapped
        except Exception as e:
            print(f"Erro na fonte {url}: {e}")
            continue

    raise HTTPException(status_code=404, detail=f"Não foi possível obter resultado para {loteria}")

def _mapear_json_agressivo(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento reforçado para todas as loterias da Caixa"""
    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or 0,
        "dataApuracao": d.get("data") or d.get("dataApuracao") or "--/--/----",
        "listaDezenas": d.get("dezenas") or d.get("listaDezenas") or d.get("numeros") or [],
        "listaDezenas2": d.get("dezenas2") or d.get("segundo_sorteio") or [],
        "trevos": d.get("trevos") or d.get("listaTrevos") or [],
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "mesSorte": d.get("mesSorte") or d.get("nomeMesSorte"),
        "acumulou": d.get("acumulou") or d.get("acumulado") or False,
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or d.get("rateio") or [],
        "localGanhadores": d.get("localGanhadores") or d.get("cidades") or [],
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }
