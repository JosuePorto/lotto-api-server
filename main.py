from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional

app = FastAPI(title="SmartLotto API v3.1 - Melhorada")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def check_status():
    return {"status": "SmartLotto API v3.1 - Melhorada", "owner": "Joao"}

@app.get("/resultado/{loteria}")
def get_resultado(
    loteria: str,
    tipo: str = "ultimo",
    concurso: Optional[int] = None
):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    # Monta URL da fonte externa
    if concurso is not None:
        url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/{concurso}"
    elif tipo.lower() == "historico":
        url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"   # pode falhar
    else:
        url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest"

    try:
        response = requests.get(url, timeout=35)
        
        if response.status_code != 200:
            return {"error": f"Fonte externa retornou {response.status_code}"}

        dados = response.json()

        if isinstance(dados, list):
            # Limita para evitar resposta gigante
            return [_mapear_json_completo(item) for item in dados[-50:]]  # últimos 50 concursos

        return _mapear_json_completo(dados)

    except Exception as e:
        return {"error": f"Erro na requisição: {str(e)}"}


def _mapear_json_completo(d: dict):
    return {
        "concurso": d.get("concurso"),
        "dataApuracao": d.get("data") or d.get("dataApuracao"),
        "listaDezenas": d.get("dezenas") or d.get("listaDezenas") or [],
        
        "valorEstimadoProximoConcurso": float(d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0),
        "valorAcumuladoProximoConcurso": float(d.get("valorAcumuladoPróximoConcurso") or 0),
        
        # Local dos ganhadores (campo que você quer)
        "localGanhadores": d.get("localGanhadores") or d.get("cidades") or d.get("ganhadoresPorLocal") or [],
        
        "listaRateio": d.get("premiacoes") or d.get("listaRateio") or [],
        
        "listaTrevos": d.get("trevos") or [],
        "nomeTimeCoracao": d.get("timeCoracao"),
        "nomeMesSorte": d.get("mesSorte"),
        
        "acumulou": d.get("acumulou", False),
        "valorArrecadado": float(d.get("valorArrecadado") or 0),
    }
