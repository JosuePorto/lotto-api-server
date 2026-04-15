from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
from typing import Optional, Dict, List, Any

app = FastAPI(title="SmartLotto API v5.1 - Engine Dinâmica")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache forte (10 minutos)
cache = {}
CACHE_DURATION = 600

# ==================== CONFIGURAÇÕES E REGRAS DINÂMICAS ====================
# Isso permite que o App mude preços e limites sem precisar de atualização na Play Store
REGRAS_LOTERIAS = {
    "megasena": {"nome": "Mega-Sena", "preco": 5.0, "min": 6, "max": 20, "universo": 60, "cor": "0xFF209869"},
    "lotofacil": {"nome": "Lotofácil", "preco": 3.0, "min": 15, "max": 20, "universo": 25, "cor": "0xFF930089"},
    "quina": {"nome": "Quina", "preco": 2.5, "min": 5, "max": 15, "universo": 80, "cor": "0xFF260085"},
    "lotomania": {"nome": "Lotomania", "preco": 3.0, "min": 50, "max": 50, "universo": 100, "cor": "0xFFF78100"},
    "loteca": {"nome": "Loteca", "preco": 3.0, "min": 14, "max": 14, "tipo": "confronto", "cor": "0xFFFF1000"},
    "diadesorte": {"nome": "Dia de Sorte", "preco": 2.5, "min": 7, "max": 15, "universo": 31, "cor": "0xFFCB812B"},
    "supersete": {"nome": "Super Sete", "preco": 2.5, "min": 7, "max": 21, "universo": 10, "cor": "0xFFABC22B"},
}

@app.get("/")
def check_status():
    return {"status": "SmartLotto API Online", "version": "5.1", "owner": "Lenha"}

@app.get("/configuracoes")
def get_config():
    """Retorna as regras de negócio para o App Flutter montar a interface"""
    return REGRAS_LOTERIAS

# ==================== LÓGICA DE MAPEAMENTO AGRESSIVO ====================
def _mapear_json(d: Dict, slug: str) -> Dict:
    """Padroniza dados de diferentes APIs e extrai confrontos da Loteca"""
    dezenas = d.get("dezenas") or d.get("listaDezenas") or d.get("numeros") or []
    
    # Tratamento especial para o formato da Loteca (Confrontos)
    confrontos = d.get("listaJogos") or d.get("jogos") or []
    
    if slug == "supersete":
        dezenas = [str(x) for x in dezenas]

    return {
        "loteria": slug,
        "concurso": d.get("concurso") or d.get("numero") or 0,
        "dataApuracao": d.get("dataApuracao") or d.get("data") or "",
        "listaDezenas": dezenas,
        "confrontos": confrontos, # Essencial para o seu app dinâmico
        "acumulou": d.get("acumulou") or d.get("acumulado") or False,
        "proximo_estimativa": float(d.get("valorEstimadoProximoConcurso") or d.get("estimativa") or 0),
        "valorAcumulado": float(d.get("valorAcumuladoProximoConcurso") or 0),
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "mesSorte": d.get("mesSorte") or d.get("nomeMesSorte"),
        "trevos": d.get("trevos") or d.get("trevo") or [],
    }

# ==================== ROTAS DE RESULTADOS ====================
@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    slug = loteria.lower().strip()
    key = f"res_{slug}_{concurso or 'latest'}"
    
    if key in cache and time.time() - cache[key]['time'] < CACHE_DURATION:
        return cache[key]['data']

    suffix = f"/{concurso}" if concurso else "/latest"
    sources = [
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}{suffix}",
        f"https://api.guidi.dev.br/loteria/{slug}/{'ultimo' if not concurso else concurso}"
    ]

    for url in sources:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                result = _mapear_json(data, slug)
                cache[key] = {'data': result, 'time': time.time()}
                return result
        except:
            continue

    return {"error": f"Erro ao buscar {slug}"}

@app.get("/historico/{loteria}")
def get_historico(loteria: str, limit: int = 50):
    slug = loteria.lower().strip()
    # Para histórico, buscamos sempre da fonte que suporta listas
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return [_mapear_json(item, slug) for item in data[:limit]]
    except:
        pass
    return {"error": "Histórico indisponível"}
