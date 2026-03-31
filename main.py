from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any, List
import time

app = FastAPI(title="SmartLotto API v4.0 - Ultra")

# Configuração de CORS para permitir acesso do Flutter/Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache aprimorado
cache = {}
CACHE_DURATION = 600  # Aumentado para 10 minutos

# Lista expandida de todas as modalidades da Caixa
LOTERIAS_CONFIG = {
    "megasena": {"id": "megasena", "nome": "Mega-Sena"},
    "lotofacil": {"id": "lotofacil", "nome": "Lotofácil"},
    "quina": {"id": "quina", "nome": "Quina"},
    "lotomania": {"id": "lotomania", "nome": "Lotomania"},
    "timemania": {"id": "timemania", "nome": "Timemania"},
    "duplasena": {"id": "duplasena", "nome": "Dupla Sena"},
    "diadesorte": {"id": "diadesorte", "nome": "Dia de Sorte"},
    "maismilionaria": {"id": "maismilionaria", "nome": "+Milionária"},
    "supersete": {"id": "supersete", "nome": "Super Sete"},
    "loteca": {"id": "loteca", "nome": "Loteca"}
}

@app.get("/")
def check_status():
    return {
        "status": "Online",
        "version": "4.0",
        "owner": "Joao",
        "endpoints": ["/loterias", "/resultado/{loteria}", "/historico/{loteria}"]
    }

@app.get("/loterias")
def listar_loterias():
    return {"loterias": list(LOTERIAS_CONFIG.keys())}

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    """Busca o último resultado ou um concurso específico"""
    slug = loteria.lower().strip()
    
    cache_key = f"{slug}_{concurso or 'latest'}"
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return cache[cache_key]['data']

    # Tentativa em múltiplas fontes
    suffix = concurso if concurso else "latest"
    sources = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{suffix}",
        f"https://api.guidi.dev.br/loteria/{slug}/{'ultimo' if not concurso else concurso}"
    ]

    for url in sources:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                mapped = _mapear_json_completo(data, slug)
                cache[cache_key] = {'data': mapped, 'time': time.time()}
                return mapped
        except Exception as e:
            print(f"Falha na fonte {url}: {e}")
            continue

    raise HTTPException(status_code=404, detail="Resultado não encontrado.")

@app.get("/historico/{loteria}")
def get_historico(loteria: str):
    """NOVO: Busca todos os resultados históricos de uma modalidade"""
    slug = loteria.lower().strip()
    
    # Algumas APIs usam rotas diferentes para o histórico completo
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            lista_bruta = response.json()
            # Mapeia cada item da lista
            historico = [_mapear_json_completo(item, slug) for item in lista_bruta]
            return {
                "loteria": slug,
                "total_concursos": len(historico),
                "resultados": historico
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {e}")

def _mapear_json_completo(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento ultra-robusto com campos específicos por loteria"""
    
    # Dezenas padrão
    dezenas = d.get("dezenas") or d.get("listaDezenas") or d.get("numeros") or []
    
    # Tratamento para +Milionária (Trevos)
    trevos = []
    if slug == "maismilionaria":
        trevos = d.get("trevos") or d.get("listaTrevos") or []

    # Localização de ganhadores (lista limpa)
    locais = d.get("listaMunicipioUfGanhadores") or d.get("localGanhadores") or []

    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or "--/--/----",
        "listaDezenas": dezenas,
        "listaDezenas2": d.get("dezenas2") or d.get("listaDezenas2") or [],
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoProximoConcurso") or d.get("valorEstimadoPróximoConcurso") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoProximoConcurso") or d.get("valorAcumulado") or 0),
        "acumulou": d.get("acumulado") or d.get("acumulou") or False,
        "listaRateio": d.get("listaRateio") or d.get("premiacoes") or [],
        "listaMunicipioUfGanhadores": locais,
        # Campos Extra de Modalidades Específicas
        "timeCoracao": d.get("timeCoracao") if slug == "timemania" else None,
        "mesSorte": d.get("mesSorte") if slug == "diadesorte" else None,
        "trevos": trevos,
        "dataProximoConcurso": d.get("dataProximoConcurso") or d.get("data_proximo_concurso")
    }
