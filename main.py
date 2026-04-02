from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any, List
import time

app = FastAPI(title="SmartLotto API v5.0 - Guidi Powered")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache para evitar sobrecarregar a API do Guidi
cache = {}
CACHE_DURATION = 300 

@app.get("/")
def check_status():
    return {"status": "Online", "source": "api.guidi.dev.br", "owner": "Joao"}

@app.get("/loterias")
def listar_loterias():
    # Incluindo todas as modalidades que o Guidi suporta
    return {
        "loterias": [
            "megasena", "quina", "lotofacil", "lotomania", "duplasena", 
            "timemania", "diadesorte", "federal", "loteca", "supersete", "maismilionaria"
        ]
    }

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[str] = "ultimo"):
    slug = loteria.lower().strip()
    
    # Cache Key
    cache_key = f"{slug}_{concurso}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # URL conforme a documentação que você encontrou
    url = f"https://api.guidi.dev.br/loteria/{slug}/{concurso}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            dados_brutos = response.json()
            mapped = _mapear_guidi_v5(dados_brutos, slug)
            
            cache[cache_key] = {"data": mapped, "time": time.time()}
            return mapped
        else:
            raise HTTPException(status_code=response.status_code, detail="Erro ao buscar dados no Guidi")
    except Exception as e:
        # Fallback para a fonte secundária caso o Guidi falhe
        return {"error": f"Falha na conexão: {str(e)}"}

def _mapear_guidi_v5(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento especializado para a API Guidi, com suporte a Loteca"""
    
    # A Loteca não tem 'dezenas', ela tem 'jogos'
    dezenas = d.get("listaDezenas") or d.get("dezenas") or []
    
    # Se for Loteca, capturamos a lista de confrontos
    jogos_loteca = d.get("listaJogos") or []

    return {
        "loteria": slug,
        "concurso": d.get("numero") or d.get("concurso") or 0,
        "dataApuracao": d.get("data") or d.get("dataApuracao") or "--/--/----",
        "listaDezenas": dezenas,
        "listaJogos": jogos_loteca, # Novo campo para a Loteca
        "acumulou": d.get("acumulou") or False,
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoProximoConcurso") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or [],
        "listaMunicipioUfGanhadores": d.get("listaMunicipioUfGanhadores") or [],
        # Campos Específicos
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "mesSorte": d.get("mesSorte") or d.get("nomeMesSorte"),
        "trevos": d.get("listaTrevos") or d.get("trevos") or [],
        "dataProximoConcurso": d.get("dataProximoConcurso") or ""
    }
