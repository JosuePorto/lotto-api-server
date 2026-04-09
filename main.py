from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import time

from data_fetcher import DataFetcher
from api_cache import LoteriasCache

app = FastAPI(title="SmartLotto API v5.0 - Estável")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias
fetcher = DataFetcher()
cache = LoteriasCache()

# Cache em memória (rápido)
mem_cache = {}
MEM_CACHE_DURATION = 300  # 5 minutos

# Lista de loterias suportadas
LOTERIAS = [
    "megasena", "lotofacil", "quina", "lotomania", "timemania",
    "duplasena", "diadesorte", "maismilionaria", "supersete", "loteca"
]

@app.get("/")
def root():
    return {
        "status": "SmartLotto API v5.0 - Estável",
        "message": "API com cache persistente e fallback",
        "loterias": LOTERIAS,
        "cache_info": "Resultados salvos localmente para fallback"
    }

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[int] = None):
    """Endpoint principal com cache e fallback"""
    
    slug = loteria.lower().replace("-", "").replace(" ", "")
    
    if slug not in LOTERIAS:
        raise HTTPException(status_code=404, detail="Loteria não encontrada")
    
    cache_key = f"{slug}_{concurso or 'ultimo'}"
    
    # 1. Tenta cache em memória (mais rápido)
    if cache_key in mem_cache and time.time() - mem_cache[cache_key]['time'] < MEM_CACHE_DURATION:
        print(f"📦 Cache memória para {slug}")
        return mem_cache[cache_key]['data']
    
    # 2. Tenta buscar dados atualizados
    try:
        dados = fetcher.buscar(slug)
        
        # Salva nos caches
        mem_cache[cache_key] = {"data": dados, "time": time.time()}
        cache.salvar(slug, dados)
        
        return dados
        
    except Exception as e:
        print(f"❌ Falha ao buscar {slug}: {e}")
        
        # 3. Fallback: tenta cache persistente
        dados_cache = cache.carregar(slug)
        if dados_cache:
            print(f"🔄 Fallback: usando cache de {slug}")
            return {
                **dados_cache,
                "source": "cache",
                "warning": "Dados em cache - pode estar desatualizado"
            }
        
        # 4. Se tudo falhou, retorna erro
        raise HTTPException(
            status_code=503,
            detail=f"Não foi possível obter dados para {slug}. Tente novamente mais tarde."
        )

@app.get("/loterias")
def listar_loterias():
    return {"loterias": LOTERIAS}

@app.get("/cache/status")
def cache_status():
    """Verifica o status do cache"""
    status = {}
    for slug in LOTERIAS:
        dados = cache.carregar(slug, max_age_hours=48)
        status[slug] = "✅ em cache" if dados else "❌ sem cache"
    return status
