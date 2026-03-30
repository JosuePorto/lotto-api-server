from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, List, Dict, Any

app = FastAPI(title="SmartLotto API v3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== ROTAS ======================

@app.get("/")
def check_status():
    return {"status": "SmartLotto API v3.1 - Melhorada", "owner": "Joao"}

# Rota principal melhorada
@app.get("/resultado/{loteria}")
def get_resultado(
    loteria: str,
    tipo: str = "ultimo",           # ultimo ou historico
    concurso: Optional[int] = None   # para buscar concurso específico
):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    # Monta a URL da fonte externa
    if concurso:
        url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{concurso}"
    elif tipo == "historico":
        url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    else:
        url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest"

    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return {"error": f"Fonte externa retornou {response.status_code}"}

        dados = response.json()

        # Se for lista (histórico completo)
        if isinstance(dados, list):
            return [_mapear_json_completo(item) for item in dados]

        # Se for resultado único
        return _mapear_json_completo(dados)

    except Exception as e:
        return {"error": f"Erro ao buscar dados: {str(e)}"}


# ====================== FUNÇÃO DE MAPEAMENTO MELHORADA ======================

def _mapear_json_completo(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "concurso": d.get("concurso"),
        "dataApuracao": d.get("data") or d.get("dataApuracao"),
        "listaDezenas": d.get("dezenas") or d.get("listaDezenas"),
        
        # Premiação e acumulação
        "valorEstimadoProximoConcurso": d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0.0,
        "valorAcumuladoProximoConcurso": d.get("valorAcumuladoPróximoConcurso") or 0.0,
        
        # Locais dos ganhadores (o que você pediu)
        "localGanhadores": d.get("localGanhadores") or d.get("cidades") or [],
        
        # Informações extras
        "listaRateio": d.get("premiacoes") or d.get("listaRateio") or [],
        "listaTrevos": d.get("trevos"),
        "nomeTimeCoracao": d.get("timeCoracao"),
        "nomeMesSorte": d.get("mesSorte"),
        
        # Campos adicionais úteis
        "acumulou": d.get("acumulou", False),
        "valorArrecadado": d.get("valorArrecadado", 0),
    }
