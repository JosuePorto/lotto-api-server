from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any
import time

app = FastAPI(title="SmartLotto API v4.5 - Agressiva")

# CORS para o Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache simples
cache = {}
CACHE_DURATION = 300  # 5 minutos

@app.get("/")
def check_status():
    return {
        "status": "SmartLotto API v4.5 - Agressiva",
        "owner": "Joao",
        "message": "Mapeamento reforçado + Cache + Fallback"
    }

@app.get("/loterias")
def listar_loterias():
    return {
        "loterias": [
            "megasena", "lotofacil", "quina", "lotomania",
            "timemania", "duplasena", "diadesorte",
            "maismilionaria", "supersete", "loteca"
        ]
    }

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    slug = loteria.lower().strip()

    # Cache
    cache_key = f"res_{slug}_{concurso or 'ultimo'}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    suffix = str(concurso) if concurso else "latest"

    # Fontes em ordem de prioridade
    sources = [
        f"https://api.guidi.dev.br/loteria/{slug}/ultimo",
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{suffix}",
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest",
    ]

    for url in sources:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()

                # Se vier lista, pega o último resultado
                if isinstance(data, list) and data:
                    data = data[-1]

                mapped = _mapear_json_agressivo(data, slug)

                # Salva no cache
                cache[cache_key] = {"data": mapped, "time": time.time()}
                return mapped

        except Exception as e:
            print(f"[ERRO] Fonte {url} falhou: {e}")
            continue

    raise HTTPException(status_code=404, detail=f"Não foi possível obter resultado para {loteria}")

@app.get("/historico/{loteria}")
def get_historico(loteria: str):
    slug = loteria.lower().strip()
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"

    try:
        response = requests.get(url, timeout=25)
        if response.status_code == 200:
            lista_bruta = response.json()
            return {
                "loteria": slug,
                "quantidade": len(lista_bruta),
                "resultados": [_mapear_json_agressivo(item, slug) for item in lista_bruta[-50:]]  # últimos 50
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _mapear_json_agressivo(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento reforçado - tenta várias chaves possíveis"""
    dezenas = d.get("listaDezenas") or d.get("dezenas") or d.get("numeros") or d.get("resultado") or []

    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or d.get("numeroConcurso") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or d.get("data_apuracao") or "--/--/----",
        "listaDezenas": dezenas,
        "listaDezenas2": d.get("listaDezenas2") or d.get("dezenas2") or [],
        "trevos": d.get("trevos") or d.get("listaTrevos") or [],
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "mesSorte": d.get("mesSorte") or d.get("nomeMesSorte"),
        "acumulou": d.get("acumulou") or d.get("acumulado") or False,
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or d.get("rateio") or [],
        "localGanhadores": d.get("localGanhadores") or d.get("listaMunicipioUfGanhadores") or d.get("ganhadoresPorLocal") or [],
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }
