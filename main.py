from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, Dict, Any
import time

app = FastAPI(title="SmartLotto API v5.5 - Ultra Resiliente")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[str] = "ultimo"):
    slug = loteria.lower().strip()
    # A API do Guidi usa 'ultimo' ou o número do concurso
    url = f"https://api.guidi.dev.br/loteria/{slug}/{concurso}"

    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            d = response.json()
            return _mapear_dados_blindados(d, slug)
        raise HTTPException(status_code=404, detail="Não encontrado")
    except Exception as e:
        return {"error": str(e), "loteria": slug}

def _mapear_dados_blindados(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    # Tenta encontrar a DATA em qualquer campo possível
    data_sorteio = d.get("data") or d.get("dataApuracao") or d.get("data_concurso") or ""
    
    # Tenta encontrar o PRÊMIO (Estimativa ou Acumulado) em qualquer campo
    # Essencial para resolver o erro de R$ 0,00
    estimativa = (
        d.get("valorEstimadoProximoConcurso") or 
        d.get("estimativa") or 
        d.get("valor_estimado_proximo_concurso") or 0
    )
    acumulado = (
        d.get("valorAcumuladoProximoConcurso") or 
        d.get("valor_acumulado") or 
        d.get("acumulado_proximo_concurso") or 0
    )

    return {
        "loteria": slug,
        "concurso": int(d.get("numero") or d.get("concurso") or 0),
        "data": data_sorteio,
        "dezenas": d.get("listaDezenas") or d.get("dezenas") or [],
        "listaJogos": d.get("listaJogos") or [], # Para a LOTECA
        "trevos": d.get("listaTrevos") or d.get("trevos") or [], # Para +MILIONÁRIA
        "acumulou": d.get("acumulado") or d.get("acumulou") or False,
        "estimativa": float(estimativa),
        "acumulado": float(acumulado),
        "rateio": d.get("listaRateio") or d.get("premiacoes") or [],
        "ganhadores_locais": d.get("listaMunicipioUfGanhadores") or d.get("local_ganhadores") or [],
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "mesSorte": d.get("mesSorte") or d.get("nomeMesSorte"),
    }
