from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional

app = FastAPI(title="SmartLotto API v3.5 - Inteligente")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def check_status():
    return {"status": "SmartLotto API v3.5 - Inteligente", "owner": "Joao"}

@app.get("/resultado/{loteria}")
def get_resultado(loteria: str):
    slug = loteria.lower().replace("-", "").replace(" ", "")

    # Fontes em ordem de prioridade
    sources = [
        f"https://api.guidi.dev.br/loteria/{slug}/ultimo",
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest",
        f"https://loteriascaixa-api.herokuapp.com/api/{slug}",
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                data = r.json()
                
                # Se for lista, pega o último
                if isinstance(data, list) and data:
                    data = data[-1]

                # Mapeamento inteligente
                return {
                    "concurso": data.get("concurso") or data.get("numero"),
                    "dataApuracao": data.get("data") or data.get("dataApuracao") or data.get("data_sorteio"),
                    "listaDezenas": data.get("dezenas") or data.get("listaDezenas") or data.get("numeros") or [],
                    "listaDezenas2": data.get("dezenas2") or [],
                    "valorEstimadoProximoConcurso": float(data.get("valorEstimadoPróximoConcurso") or data.get("estimativa") or 0),
                    "valorAcumuladoProximoConcurso": float(data.get("valorAcumuladoProximoConcurso") or 0),
                    "localGanhadores": data.get("localGanhadores") or data.get("cidades") or [],
                    "listaRateio": data.get("premiacoes") or data.get("listaRateio") or [],
                    "acumulou": data.get("acumulou", len(data.get("listaRateio", [])) == 0),
                }
        except:
            continue

    return {"error": f"Não foi possível obter resultado para {loteria}. Tente novamente mais tarde."}
