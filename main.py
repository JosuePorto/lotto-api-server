import requests
from typing import Dict, Any, Optional

class LoteriasAPI:
    """Cliente unificado para múltiplas APIs de loterias"""
    
    # Fontes de dados
    FONTES = {
        "guididev": "https://api.guidi.dev.br/loteria/{slug}/ultimo",
        "loteriascaixa": "https://loteriascaixa-api.herokuapp.com/api/{slug}/latest",
        "loteriasapi": "https://loterias-api.com/api/{slug}/latest",
    }
    
    def buscar_resultado(self, slug: str) -> Dict[str, Any]:
        """Busca resultado da primeira fonte que responder"""
        
        for nome, url_template in self.FONTES.items():
            url = url_template.format(slug=slug)
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    dados = response.json()
                    return self._normalizar_dados(dados, slug, nome)
            except Exception as e:
                print(f"Erro na fonte {nome}: {e}")
                continue
        
        raise Exception(f"Nenhuma fonte retornou dados para {slug}")
    
    def _normalizar_dados(self, dados: Dict, slug: str, fonte: str) -> Dict:
        """Normaliza os dados para o formato padrão"""
        
        resultado = {
            "loteria": slug,
            "concurso": 0,
            "dataApuracao": "",
            "listaDezenas": [],
            "listaDezenas2": [],
            "trevos": [],
            "timeCoracao": None,
            "mesSorte": None,
            "acumulou": False,
            "valorEstimadoProximoConcurso": 0.0,
            "valorAcumuladoProximoConcurso": 0.0,
            "listaRateio": [],
        }
        
        # ============================================
        # Mapeamento GUIDIDEV (recomendado)
        # ============================================
        if fonte == "guididev":
            resultado["concurso"] = dados.get("concurso", 0)
            resultado["dataApuracao"] = dados.get("data", "")
            resultado["listaDezenas"] = dados.get("dezenas", [])
            resultado["listaDezenas2"] = dados.get("dezenas2", [])
            resultado["trevos"] = dados.get("trevos", [])
            resultado["timeCoracao"] = dados.get("time_coracao") or dados.get("nomeTimeCoracao")
            resultado["mesSorte"] = dados.get("mes_sorte") or dados.get("nomeMesSorte")
            resultado["acumulou"] = dados.get("acumulou", False)
            resultado["valorEstimadoProximoConcurso"] = float(dados.get("estimativa", 0))
            resultado["valorAcumuladoProximoConcurso"] = float(dados.get("valorAcumulado", 0))
            resultado["listaRateio"] = dados.get("rateio", [])
        
        # ============================================
        # Mapeamento LOTERIASCAIXA-API
        # ============================================
        elif fonte == "loteriascaixa":
            resultado["concurso"] = dados.get("concurso", 0)
            resultado["dataApuracao"] = dados.get("data_apuracao", "")
            resultado["listaDezenas"] = dados.get("dezenas", [])
            
            # Tratamento especial para Dupla Sena
            if slug == "duplasena" and "dezenas" in dados and len(dados["dezenas"]) == 12:
                resultado["listaDezenas"] = dados["dezenas"][:6]
                resultado["listaDezenas2"] = dados["dezenas"][6:12]
            else:
                resultado["listaDezenas2"] = dados.get("dezenas2", [])
            
            resultado["trevos"] = dados.get("trevos", [])
            resultado["timeCoracao"] = dados.get("time_coracao")
            resultado["mesSorte"] = dados.get("mes_sorte")
            resultado["acumulou"] = dados.get("acumulou", False)
            resultado["valorEstimadoProximoConcurso"] = float(dados.get("estimativa", 0))
            resultado["valorAcumuladoProximoConcurso"] = float(dados.get("acumulado", 0))
            resultado["listaRateio"] = dados.get("premiacoes", [])
        
        return resultado
