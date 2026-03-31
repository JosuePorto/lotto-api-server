from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any, List
import time

app = FastAPI(title="SmartLotto API v4.0 - Ultra")

# Configuração de CORS para o Flutter não ter erro de bloqueio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache inteligente em memória
cache = {}
CACHE_DURATION = 600  # 10 minutos para resultados recentes
HISTORY_CACHE_DURATION = 3600  # 1 hora para histórico completo

@app.get("/")
def check_status():
    return {
        "status": "SmartLotto API v4.0 - Online",
        "owner": "Joao",
        "endpoints": ["/loterias", "/resultado/{loteria}", "/historico/{loteria}"]
    }

@app.get("/loterias")
def listar_loterias():
    """Lista todas as modalidades suportadas pela API"""
    return {
        "loterias": [
            "megasena", "lotofacil", "quina", "lotomania", 
            "timemania", "duplasena", "diadesorte", 
            "maismilionaria", "supersete", "loteca"
        ]
    }

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    """Busca o último resultado ou um concurso específico com redundância"""
    slug = loteria.lower().strip()
    suffix = concurso if concurso else "latest"
    
    # Validação de Cache
    cache_key = f"res_{slug}_{suffix}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Fontes de dados (Redundância)
    sources = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{suffix}",
        f"https://api.guidi.dev.br/loteria/{slug}/{'ultimo' if not concurso else concurso}"
    ]

    for url in sources:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = _mapear_json_completo(response.json(), slug)
                cache[cache_key] = {"data": data, "time": time.time()}
                return data
        except Exception:
            continue

    raise HTTPException(status_code=404, detail="Resultado não encontrado nas fontes oficiais.")

@app.get("/historico/{loteria}")
def get_historico(loteria: str):
    """NOVO: Busca o histórico completo de resultados de uma modalidade"""
    slug = loteria.lower().strip()
    
    cache_key = f"hist_{slug}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < HISTORY_CACHE_DURATION:
        return cache[cache_key]['data']

    # URL para histórico completo
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            lista_bruta = response.json()
            # Mapeia cada item da lista para manter o padrão SmartLotto
            historico = [_mapear_json_completo(item, slug) for item in lista_bruta]
            
            result = {
                "loteria": slug,
                "total_concursos": len(historico),
                "resultados": historico
            }
            
            cache[cache_key] = {"data": result, "time": time.time()}
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico completo: {str(e)}")

def _mapear_json_completo(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeia os dados brutos das APIs externas para o formato padrão do SmartLotto Pro"""
    
    # Extração de dezenas (lida com diferentes formatos de API)
    dezenas = d.get("dezenas") or d.get("listaDezenas") or d.get("numeros") or []
    
    # Ganhadores por localidade
    locais = d.get("listaMunicipioUfGanhadores") or d.get("localGanhadores") or []

    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or "--/--/----",
        "listaDezenas": dezenas,
        "listaDezenas2": d.get("dezenas2") or d.get("listaDezenas2") or [],
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoProximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or d.get("valorAcumulado") or 0),
        "acumulou": d.get("acumulado") or d.get("acumulou") or False,
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or [],
        "listaMunicipioUfGanhadores": locais,
        # Dados específicos por modalidade
        "timeCoracao": d.get("timeCoracao") if slug == "timemania" else None,
        "mesSorte": d.get("mesSorte") if slug == "diadesorte" else None,
        "trevos": d.get("trevos") or d.get("listaTrevos") if slug == "maismilionaria" else [],
        "dataProximoConcurso": d.get("dataProximoConcurso") or d.get("data_proximo_concurso")
    }
