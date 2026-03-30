from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any
import time

app = FastAPI(title="SmartLotto API v3.5 - Potencializada")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache simples em memória
cache = {}
CACHE_DURATION = 300  # 5 minutos em segundos

@app.get("/")
def check_status():
    return {
        "status": "SmartLotto API v3.5 - Potencializada",
        "owner": "Joao",
        "message": "API pronta para Mega-Sena, Lotofácil, Quina, Lotomania, Dupla Sena, Loteca e mais"
    }

@app.get("/loterias")
def listar_loterias():
    """Lista todas as loterias suportadas"""
    return {
        "loterias": [
            "megasena", "lotofacil", "quina", "lotomania", 
            "timemania", "duplasena", "diadesorte", 
            "maismilionaria", "supersete", "loteca"
        ]
    }

@app.get("/resultado/{loteria}")
def get_resultado(
    loteria: str,
    tipo: str = "ultimo",
    concurso: Optional[int] = None
):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    # Cache key
    cache_key = f"{slug}_{tipo}_{concurso or 'ultimo'}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Fontes em ordem de prioridade
    sources = [
        f"https://api.guidi.dev.br/loteria/{slug}/ultimo",
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest",
    ]

    for url in sources:
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                data = response.json()

                # Se vier lista, pega o último item
                if isinstance(data, list) and data:
                    data = data[-1]

                mapped = _mapear_json_completo(data)
                
                # Salva no cache
                cache[cache_key] = {'data': mapped, 'time': time.time()}
                return mapped

        except Exception as e:
            print(f"Erro na fonte {url}: {e}")
            continue

    return {"error": f"Não foi possível obter o resultado para {loteria}. Tente novamente mais tarde."}


def _mapear_json_completo(d: Dict[str, Any]) -> Dict[str, Any]:
    """Mapeamento robusto que tenta vários nomes de campos"""
    return {
        "concurso": d.get("concurso") or d.get("numero") or d.get("Concurso"),
        "dataApuracao": d.get("data") or d.get("dataApuracao") or d.get("Data"),
        "listaDezenas": d.get("dezenas") or d.get("listaDezenas") or d.get("numeros") or [],
        "listaDezenas2": d.get("dezenas2") or [],
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "localGanhadores": d.get("localGanhadores") or d.get("cidades") or d.get("ganhadoresPorLocal") or [],
        "listaRateio": d.get("premiacoes") or d.get("listaRateio") or [],
        "acumulou": d.get("acumulou", True),
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }
