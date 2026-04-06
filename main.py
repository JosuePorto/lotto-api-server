import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

app = FastAPI(title="SmartLotto API v6.0 - Edição Profissional")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# TOKEN OFICIAL
TOKEN = "alOIXlglyUweMDv"

@app.get("/resultado/{loteria}")
def get_pro_result(loteria: str, concurso: Optional[str] = None):
    slug = loteria.lower().strip()
    
    # URL da V2 Profissional
    url = f"https://apiloterias.com.br/app/v2/resultado?loteria={slug}&token={TOKEN}"
    
    # Se o usuário pedir um concurso específico (Histórico)
    if concurso and concurso != "ultimo":
        url += f"&concurso={concurso}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            return _mapear_v2_pro(dados, slug)
        
        raise HTTPException(status_code=response.status_code, detail="Erro na API Pro")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _mapear_v2_pro(d: Dict[str, Any], slug: str) -> Dict[str, Any]:
    """Mapeamento focado na estrutura da APILoterias V2"""
    
    # A V2 usa nomes de campos muito claros
    return {
        "loteria": slug,
        "concurso": d.get("numero_concurso", 0),
        "data": d.get("data_concurso", "--/--/----"),
        "dezenas": d.get("dezenas", []),
        "listaJogos": d.get("jogos", []), # Mapeamento para Loteca
        "acumulou": d.get("acumulou", False),
        "estimativa": float(d.get("valor_estimado_proximo_concurso") or 0),
        "acumulado": float(d.get("valor_acumulado") or 0),
        "rateio": d.get("premiacoes", []),
        "ganhadores_locais": d.get("local_ganhadores", []), # Onde saiu o prêmio!
        "trevos": d.get("trevos", []), # +Milionária
        "timeCoracao": d.get("nome_time_coracao"), # Timemania
        "mesSorte": d.get("nome_mes_sorte"), # Dia de Sorte
        "proximo_concurso": d.get("data_proximo_concurso")
    }
