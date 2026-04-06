import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TOKEN = "alOIXlglyUweMDv" # Seu Token Profissional

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[str] = "ultimo"):
    slug = loteria.lower().strip()
    url = f"https://apiloterias.com.br/app/v2/resultado?loteria={slug}&token={TOKEN}"
    
    if concurso and concurso != "ultimo":
        url += f"&concurso={concurso}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return _mapear_universal(response.json(), slug)
        raise HTTPException(status_code=404, detail="Erro na fonte de dados")
    except Exception as e:
        return {"error": str(e)}

def _mapear_universal(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    # MAPEAMENTO AGRESSIVO: Tenta todas as chaves da API Paga e Gratuita
    num = d.get("numero_concurso") or d.get("numero") or d.get("concurso") or 0
    dt = d.get("data_concurso") or d.get("data") or d.get("dataApuracao") or "--/--/----"
    
    # Busca os jogos da Loteca (campo 'jogos' na API Paga)
    jogos = d.get("jogos") or d.get("listaJogos") or []
    
    # Valores financeiros
    est = d.get("valor_estimado_proximo_concurso") or d.get("valorEstimadoProximoConcurso") or 0
    acu = d.get("valor_acumulado") or d.get("valorAcumuladoProximoConcurso") or 0

    return {
        "loteria": slug,
        "concurso": int(num),
        "data": dt,
        "dezenas": d.get("dezenas") or d.get("listaDezenas") or [],
        "listaJogos": jogos, 
        "acumulou": d.get("acumulou") or d.get("acumulado") or False,
        "estimativa": float(est),
        "acumulado": float(acu),
        "rateio": d.get("premiacoes") or d.get("listaRateio") or [],
        "ganhadores_locais": d.get("local_ganhadores") or d.get("listaMunicipioUfGanhadores") or [],
        "timeCoracao": d.get("nome_time_coracao") or d.get("timeCoracao") or d.get("nomeTimeCoracao"),
    }
