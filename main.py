from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any, List
import time

app = FastAPI(title="SmartLotto API v4.0 - Ultra")

# Configuração de CORS para o Flutter acessar sem bloqueios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache em memória para não sobrecarregar as fontes externas
cache = {}
CACHE_DURATION = 600  # 10 minutos

@app.get("/")
def status():
    return {
        "api": "SmartLotto Pro",
        "status": "Online",
        "endpoints_disponiveis": ["/loterias", "/resultado/{loteria}", "/historico/{loteria}"]
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
    """Busca o último resultado ou um concurso específico"""
    slug = loteria.lower().strip()
    suffix = concurso if concurso else "latest"
    
    # Check Cache
    cache_key = f"{slug}_{suffix}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Fontes redundantes
    urls = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{suffix}",
        f"https://api.guidi.dev.br/loteria/{slug}/{'ultimo' if not concurso else concurso}"
    ]

    for url in urls:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = _mapear_json_completo(r.json(), slug)
                cache[cache_key] = {"data": data, "time": time.time()}
                return data
        except:
            continue

    raise HTTPException(status_code=404, detail="Resultado não encontrado.")

@app.get("/historico/{loteria}")
def get_historico(loteria: str):
    """NOVO: Busca TODOS os resultados já realizados de uma modalidade"""
    slug = loteria.lower().strip()
    
    # URL para histórico completo (LoteriasCaixa API suporta isso na rota base)
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            lista_bruta = r.json()
            # Mapeia cada item da lista para o formato SmartLotto
            historico = [_mapear_json_completo(item, slug) for item in lista_bruta]
            return {
                "loteria": slug,
                "total_resultados": len(historico),
                "resultados": historico
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar histórico: {e}")

def _mapear_json_completo(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento ultra-robusto para todas as modalidades"""
    return {
        "concurso": d.get("concurso") or d.get("numero") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or "--/--/----",
        "listaDezenas": d.get("listaDezenas") or d.get("dezenas") or d.get("numeros") or [],
        "listaDezenas2": d.get("dezenas2") or d.get("listaDezenas2") or [],
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoProximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or d.get("acumulado") or 0),
        "acumulou": d.get("acumulado") or d.get("acumulou") or False,
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or [],
        "listaMunicipioUfGanhadores": d.get("listaMunicipioUfGanhadores") or d.get("localGanhadores") or [],
        # Campos Específicos
        "timeCoracao": d.get("timeCoracao") if slug == "timemania" else None,
        "mesSorte": d.get("mesSorte") if slug == "diadesorte" else None,
        "trevos": d.get("trevos") if slug == "maismilionaria" else [],
        "dataProximoConcurso": d.get("dataProximoConcurso") or d.get("data_proximo_concurso")
    }
