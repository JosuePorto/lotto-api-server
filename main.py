from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota para saber se o servidor acordou
@app.get("/")
def check_status():
    return {"status": "SmartLotto API v3.0 - Full History", "owner": "Joao"}

# Rota Única Inteligente: Busca último ou histórico
@app.get("/resultado/{loteria}")
def get_dados(loteria: str, tipo: str = "ultimo"):
    slug = loteria.lower().replace("-", "")
    
    # Se pedir 'ultimo', busca o sorteio mais recente
    # Se pedir 'historico', a API comunitária retorna a lista de todos
    suffix = "/latest" if tipo == "ultimo" else ""
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}{suffix}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            dados = response.json()
            
            # Se for uma lista (histórico), mapeia cada item
            if isinstance(dados, list):
                return [_mapear_json(item) for item in dados]
            
            # Se for objeto único (último resultado)
            return _mapear_json(dados)
            
        return {"error": f"Fonte externa retornou {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# Função de limpeza: Deixa o JSON mastigadinho para o seu Flutter
def _mapear_json(d):
    return {
        "concurso": d.get("concurso"),
        "dataApuracao": d.get("data"),
        "listaDezenas": d.get("dezenas"),
        "valorEstimadoProximoConcurso": d.get("valorEstimadoPróximoConcurso") or d.get("estimativa") or 0.0,
        "valorAcumuladoProximoConcurso": d.get("valorAcumuladoPróximoConcurso") or 0.0,
        "listaTrevos": d.get("trevos"),
        "nomeTimeCoracao": d.get("timeCoracao"),
        "nomeMesSorte": d.get("mesSorte"),
        "listaRateio": d.get("premiacoes")
    }
