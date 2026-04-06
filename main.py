import os
import time
import logging
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

# Configuração de Log (Para você saber exatamente o que quebra no Render)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartLotto_Elite")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chaves de API - Use variáveis de ambiente no Render por segurança!
# Se não houver token, o sistema usa um valor padrão ou avisa.
APILOTERIAS_TOKEN = os.getenv("APILOTERIAS_TOKEN", "alOIXlglyUweMDv")

class LotteryEngine:
    """Motor de busca com redundância (Fallback)"""
    
    @staticmethod
    def get_data(loteria: str, concurso: str):
        # 1ª TENTATIVA: API do Guidi (Rápida e Gratuita)
        try:
            url_guidi = f"https://api.guidi.dev.br/loteria/{loteria}/{concurso}"
            response = requests.get(url_guidi, timeout=10)
            if response.status_code == 200:
                logger.info(f"Fonte Guidi OK: {loteria}")
                return response.json(), "guidi"
        except Exception as e:
            logger.warning(f"Guidi falhou: {e}")

        # 2ª TENTATIVA (FALLBACK): APILoterias V2 (Profissional/Paga)
        try:
            url_pro = f"https://apiloterias.com.br/app/v2/resultado?loteria={loteria}&token={APILOTERIAS_TOKEN}"
            response = requests.get(url_pro, timeout=10)
            if response.status_code == 200:
                logger.info(f"Fonte Pro OK: {loteria}")
                return response.json(), "pro"
        except Exception as e:
            logger.error(f"Todas as fontes falharam: {e}")
            
        return None, None

@app.get("/resultado/{loteria}")
def fetch_lotto(loteria: str, concurso: Optional[str] = "ultimo"):
    raw_data, source = LotteryEngine.get_data(loteria, concurso)
    
    if not raw_data:
        raise HTTPException(status_code=503, detail="Serviços da Caixa indisponíveis no momento.")

    return _normalize_response(raw_data, loteria, source)

def _normalize_response(d: Dict[str, Any], slug: str, source: str) -> Dict[str, Any]:
    """Normaliza campos de diferentes APIs para um padrão único para o Flutter"""
    
    # Mapeamento de chaves conforme a fonte
    if source == "guidi":
        num = d.get("numero")
        data = d.get("data")
        estimativa = d.get("valorEstimadoProximoConcurso")
        acumulado = d.get("valorAcumuladoProximoConcurso")
        jogos = d.get("listaJogos", [])
        rateio = d.get("listaRateio", [])
    else: # Fonte "pro" (APILoterias)
        num = d.get("numero_concurso")
        data = d.get("data_concurso")
        estimativa = d.get("valor_estimado_proximo_concurso")
        acumulado = d.get("valor_acumulado")
        jogos = [] # Adicionar se a Pro suportar
        rateio = d.get("premiacoes", [])

    return {
        "loteria": slug,
        "concurso": int(num or 0),
        "data": data or "--/--/----",
        "dezenas": d.get("dezenas") or d.get("listaDezenas") or [],
        "listaJogos": jogos,
        "acumulou": d.get("acumulou", False) or d.get("acumulado", False),
        "estimativa": float(estimativa or 0),
        "acumulado": float(acumulado or 0),
        "rateio": rateio,
        "timeCoracao": d.get("timeCoracao") or d.get("nomeTimeCoracao"),
        "trevos": d.get("trevos") or d.get("listaTrevos") or [],
        "source_engine": source # Debug para você saber qual API respondeu
    }
