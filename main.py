from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any, List
import time

app = FastAPI(title="SmartLotto API v4.5 - Agressiva")

# Habilita CORS para o Flutter não travar
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
    return {"status": "SmartLotto API v4.5 Live", "mode": "Aggressive Mapping"}

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
    suffix = concurso if concurso else "latest"
    
    # Busca no Cache
    cache_key = f"res_{slug}_{suffix}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Fontes em ordem de estabilidade
    sources = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{suffix}",
        f"https://api.guidi.dev.br/loteria/{slug}/{'ultimo' if not concurso else concurso}"
    ]

    for url in sources:
        try:
            response = requests.get(url, timeout=12)
            if response.status_code == 200:
                data = _mapear_json_agressivo(response.json(), slug)
                cache[cache_key] = {"data": data, "time": time.time()}
                return data
        except Exception:
            continue

    raise HTTPException(status_code=404, detail="Dados não encontrados em nenhuma fonte.")

@app.get("/historico/{loteria}")
def get_historico(loteria: str):
    """Busca o histórico completo mapeado"""
    slug = loteria.lower().strip()
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    
    try:
        response = requests.get(url, timeout=25)
        if response.status_code == 200:
            lista_bruta = response.json()
            return {
                "loteria": slug,
                "resultados": [_mapear_json_agressivo(item, slug) for item in lista_bruta]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _mapear_json_agressivo(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento Reforçado: Tenta múltiplas chaves para cada campo crítico"""
    
    # 1. DEZENAS (Padrão)
    dezenas = d.get("listaDezenas") or d.get("dezenas") or d.get("numeros") or d.get("resultado") or []
    
    # 2. TREVOS (+MILIONÁRIA) - Onde a maioria das APIs falha
    trevos = d.get("trevos") or d.get("listaTrevos") or d.get("dezenasSecundarias") or []
    
    # 3. TIME DO CORAÇÃO (TIMEMANIA)
    time_coracao = d.get("timeCoracao") or d.get("nomeTimeCoracao") or d.get("time_coracao")
    
    # 4. MÊS DE SORTE (DIA DE SORTE)
    mes_sorte = d.get("mesSorte") or d.get("nomeMesSorte") or d.get("mes_sorte")

    # 5. GANHADORES POR LOCALIDADE (CREDIBILIDADE)
    locais = d.get("listaMunicipioUfGanhadores") or d.get("localGanhadores") or d.get("ganhadoresPorLocal") or []

    # 6. ESTIMATIVA E ACUMULADO (DINHEIRO)
    estimativa = d.get("valorEstimadoProximoConcurso") or d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0
    acumulado = d.get("valorAcumuladoProximoConcurso") or d.get("valorAcumulado") or 0

    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or d.get("numeroConcurso") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or d.get("data_apuracao") or "--/--/----",
        "listaDezenas": dezenas,
        "trevos": trevos,
        "timeCoracao": str(time_coracao) if time_coracao else None,
        "mesSorte": str(mes_sorte) if mes_sorte else None,
        "acumulou": d.get("acumulado") or d.get("acumulou") or False,
        "valorEstimadoProximoConcurso": float(estimativa),
        "valorAcumuladoProximoConcurso": float(acumulado),
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or d.get("rateio") or [],
        "listaMunicipioUfGanhadores": locais,
        "dataProximoConcurso": d.get("dataProximoConcurso") or d.get("dataProximoSorteio") or ""
    }
