from fastapi import FastAPI, HTTPException
import requests
from typing import Optional, Dict, Any

app = FastAPI()

# ... (Middleware CORS permanece igual)

TOKEN = "alOIXlglyUweMDv" # Seu Token Profissional

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str, concurso: Optional[str] = "ultimo"):
    slug = loteria.lower().strip()
    # URL da API Profissional
    url = f"https://apiloterias.com.br/app/v2/resultado?loteria={slug}&token={TOKEN}"
    
    if concurso and concurso != "ultimo":
        url += f"&concurso={concurso}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            d = response.json()
            return _mapear_universal(d, slug)
        raise HTTPException(status_code=404, detail="Erro na fonte")
    except Exception as e:
        return {"error": str(e)}

def _mapear_universal(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeia qualquer chave vinda da API Paga ou Gratuita"""
    
    # Tenta todas as variações de chaves comuns
    concurso = d.get("numero_concurso") or d.get("numero") or d.get("concurso") or 0
    data = d.get("data_concurso") or d.get("data") or d.get("dataApuracao") or "--/--/----"
    jogos = d.get("jogos") or d.get("listaJogos") or []
    
    # Valores financeiros (Caça as chaves da API Paga)
    estimativa = d.get("valor_estimado_proximo_concurso") or d.get("valorEstimadoProximoConcurso") or 0
    acumulado = d.get("valor_acumulado") or d.get("valorAcumuladoProximoConcurso") or 0

    return {
        "loteria": slug,
        "concurso": int(concurso),
        "data": data,
        "dezenas": d.get("dezenas") or d.get("listaDezenas") or [],
        "listaJogos": jogos, 
        "acumulou": d.get("acumulou") or False,
        "estimativa": float(estimativa),
        "acumulado": float(acumulado),
        "rateio": d.get("premiacoes") or d.get("listaRateio") or [],
        "ganhadores_locais": d.get("local_ganhadores") or d.get("listaMunicipioUfGanhadores") or [],
        "timeCoracao": d.get("nome_time_coracao") or d.get("timeCoracao")
    }
