from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Permissões para o seu app Flutter não ser bloqueado (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "SmartLotto API Blindada", "v": "2.0"}

@app.get("/resultado/{modalidade}")
def get_resultado(modalidade: str):
    # Padroniza o nome para a API alternativa
    slug = modalidade.lower().replace("-", "")
    
    # ROTA ALTERNATIVA (Mais estável para Datacenters como o Render)
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}/latest"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            # Mapeamento para garantir que o seu Flutter encontre as chaves certas
            return {
                "concurso": dados.get("concurso"),
                "dataApuracao": dados.get("data"),
                "listaDezenas": dados.get("dezenas"),
                "valorEstimadoProximoConcurso": dados.get("valorEstimadoPróximoConcurso") or dados.get("estimativa"),
                "valorAcumuladoProximoConcurso": dados.get("valorAcumuladoPróximoConcurso"),
                "listaTrevos": dados.get("trevos"),
                "nomeTimeCoracao": dados.get("timeCoracao"),
                "nomeMesSorte": dados.get("mesSorte"),
                "listaRateio": dados.get("premiacoes")
            }
        
        return {"error": f"API alternativa retornou status {response.status_code}"}
        
    except Exception as e:
        return {"error": str(e)}
