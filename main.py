import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional

class CaixaScraper:
    """Scraper oficial do site da CAIXA para loterias"""
    
    # URLs oficiais
    BASE_URL = "https://loterias.caixa.gov.br/Paginas"
    
    # Mapeamento de slugs para URLs
    URLS = {
        "megasena": f"{BASE_URL}/Mega-Sena.aspx",
        "lotofacil": f"{BASE_URL}/Lotofacil.aspx",
        "quina": f"{BASE_URL}/Quina.aspx",
        "lotomania": f"{BASE_URL}/Lotomania.aspx",
        "timemania": f"{BASE_URL}/Timemania.aspx",
        "duplasena": f"{BASE_URL}/Dupla-Sena.aspx",
        "diadesorte": f"{BASE_URL}/Dia-de-Sorte.aspx",
        "maismilionaria": f"{BASE_URL}/Mais-Milionaria.aspx",
        "supersete": f"{BASE_URL}/Super-Sete.aspx",
        "loteca": f"{BASE_URL}/Loteca.aspx",
    }
    
    def get_resultado(self, slug: str, concurso: Optional[int] = None) -> Dict[str, Any]:
        """Busca resultado diretamente no site da CAIXA"""
        
        url = self.URLS.get(slug)
        if not url:
            raise Exception(f"Loteria {slug} não suportada")
        
        # Se concurso específico, adiciona parâmetro
        if concurso:
            url += f"?concurso={concurso}"
        
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extrai dados usando o método específico da loteria
            if slug == "duplasena":
                return self._parse_duplasena(soup, slug)
            elif slug == "timemania":
                return self._parse_timemania(soup, slug)
            elif slug == "diadesorte":
                return self._parse_diadesorte(soup, slug)
            elif slug == "maismilionaria":
                return self._parse_maismilionaria(soup, slug)
            else:
                return self._parse_generico(soup, slug)
                
        except Exception as e:
            raise Exception(f"Erro ao fazer scraping: {e}")
    
    # ============================================
    # DUPLA SENA (2 sorteios)
    # ============================================
    def _parse_duplasena(self, soup: BeautifulSoup, slug: str) -> Dict[str, Any]:
        resultado = self._parse_generico(soup, slug)
        
        # Busca o segundo sorteio
        segundo_sorteio = []
        
        # Tenta encontrar o segundo conjunto de números
        # Padrão do site: primeiro sorteio e segundo sorteio em divs diferentes
        segundas_dezenas = soup.find_all('ul', class_='numbers second-sorteio')
        if segundas_dezenas:
            for item in segundas_dezenas:
                numeros = item.find_all('li')
                segundo_sorteio = [n.get_text().strip() for n in numeros]
        
        # Se não achou, tenta por classe específica
        if not segundo_sorteio:
            segundas_dezenas = soup.find_all('div', class_='second-sorteio')
            if segundas_dezenas:
                numeros = segundas_dezenas[0].find_all('span', class_='numero')
                segundo_sorteio = [n.get_text().strip() for n in numeros]
        
        resultado["listaDezenas2"] = segundo_sorteio
        return resultado
    
    # ============================================
    # TIMEMANIA (Time do Coração)
    # ============================================
    def _parse_timemania(self, soup: BeautifulSoup, slug: str) -> Dict[str, Any]:
        resultado = self._parse_generico(soup, slug)
        
        time_coracao = None
        
        # Busca o time do coração
        time_element = soup.find('span', class_='time-coracao')
        if time_element:
            time_coracao = time_element.get_text().strip()
        
        # Tenta por outro seletor
        if not time_coracao:
            time_element = soup.find('div', class_='time-coracao')
            if time_element:
                time_coracao = time_element.get_text().strip()
        
        # Tenta por regex no texto
        if not time_coracao:
            text = soup.get_text()
            match = re.search(r'Time\s+do\s+Coração\s*:\s*([A-Z\s]+)', text, re.IGNORECASE)
            if match:
                time_coracao = match.group(1).strip()
        
        resultado["timeCoracao"] = time_coracao
        return resultado
    
    # ============================================
    # DIA DE SORTE (Mês da Sorte)
    # ============================================
    def _parse_diadesorte(self, soup: BeautifulSoup, slug: str) -> Dict[str, Any]:
        resultado = self._parse_generico(soup, slug)
        
        mes_sorte = None
        
        # Busca o mês da sorte
        mes_element = soup.find('span', class_='mes-sorte')
        if mes_element:
            mes_sorte = mes_element.get_text().strip()
        
        # Tenta por outro seletor
        if not mes_sorte:
            mes_element = soup.find('div', class_='mes-sorte')
            if mes_element:
                mes_sorte = mes_element.get_text().strip()
        
        # Tenta por regex
        if not mes_sorte:
            text = soup.get_text()
            match = re.search(r'Mês\s+da\s+Sorte\s*:\s*([A-ZÇÃÕ]+)', text, re.IGNORECASE)
            if match:
                mes_sorte = match.group(1).strip()
        
        resultado["mesSorte"] = mes_sorte
        return resultado
    
    # ============================================
    # +MILIONÁRIA (Trevos)
    # ============================================
    def _parse_maismilionaria(self, soup: BeautifulSoup, slug: str) -> Dict[str, Any]:
        resultado = self._parse_generico(soup, slug)
        
        trevos = []
        
        # Busca os trevos (números especiais)
        trevos_element = soup.find_all('span', class_='trevo')
        if trevos_element:
            trevos = [t.get_text().strip() for t in trevos_element]
        
        # Tenta por outro seletor
        if not trevos:
            trevos_element = soup.find_all('div', class_='trevo')
            if trevos_element:
                for t in trevos_element:
                    numeros = t.find_all('span', class_='numero')
                    trevos = [n.get_text().strip() for n in numeros]
        
        resultado["trevos"] = trevos
        return resultado
    
    # ============================================
    # PARSER GENÉRICO (para todas as loterias)
    # ============================================
    def _parse_generico(self, soup: BeautifulSoup, slug: str) -> Dict[str, Any]:
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
            "localGanhadores": [],
            "valorArrecadado": 0.0,
        }
        
        # Concurso
        concurso_elem = soup.find('span', class_='concurso')
        if concurso_elem:
            text = concurso_elem.get_text()
            match = re.search(r'\d+', text)
            if match:
                resultado["concurso"] = int(match.group())
        
        # Data
        data_elem = soup.find('span', class_='data')
        if data_elem:
            resultado["dataApuracao"] = data_elem.get_text().strip()
        
        # Números sorteados
        numeros_elem = soup.find_all('ul', class_='numbers')
        if numeros_elem:
            for ul in numeros_elem:
                itens = ul.find_all('li')
                if itens:
                    resultado["listaDezenas"] = [n.get_text().strip() for n in itens]
                    break
        
        # Se não achou números, tenta por outra classe
        if not resultado["listaDezenas"]:
            numeros_elem = soup.find_all('div', class_='numbers')
            for div in numeros_elem:
                spans = div.find_all('span', class_='numero')
                if spans:
                    resultado["listaDezenas"] = [s.get_text().strip() for s in spans]
                    break
        
        # Valor acumulado
        acumulado_elem = soup.find('span', class_='acumulado')
        if acumulado_elem:
            text = acumulado_elem.get_text()
            resultado["acumulou"] = "SIM" in text.upper() or "ACUMULOU" in text.upper()
            
            # Tenta extrair valor
            valor_match = re.search(r'R\$\s*([\d\.]+,\d{2})', text)
            if valor_match:
                valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                resultado["valorAcumuladoProximoConcurso"] = float(valor_str)
        
        # Próximo concurso (estimativa)
        estimativa_elem = soup.find('span', class_='estimativa')
        if estimativa_elem:
            text = estimativa_elem.get_text()
            valor_match = re.search(r'R\$\s*([\d\.]+,\d{2})', text)
            if valor_match:
                valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                resultado["valorEstimadoProximoConcurso"] = float(valor_str)
        
        # Rateio (premiações)
        rateio_table = soup.find('table', class_='rateio')
        if rateio_table:
            rows = rateio_table.find_all('tr')
            for row in rows[1:]:  # Pula cabeçalho
                cols = row.find_all('td')
                if len(cols) >= 3:
                    rateio_item = {
                        "descricao": cols[0].get_text().strip(),
                        "ganhadores": int(re.sub(r'\D', '', cols[1].get_text()) or 0),
                        "valorPremio": self._parse_currency(cols[2].get_text())
                    }
                    resultado["listaRateio"].append(rateio_item)
        
        return resultado
    
    def _parse_currency(self, text: str) -> float:
        """Converte texto R$ 1.234,56 para float"""
        if not text:
            return 0.0
        match = re.search(r'([\d\.]+,\d{2})', text)
        if match:
            valor_str = match.group(1).replace('.', '').replace(',', '.')
            return float(valor_str)
        return 0.0


# ============================================
# INTEGRAÇÃO COM SUA API FASTAPI
# ============================================

scraper = CaixaScraper()

def get_resultado_from_scraper(loteria: str, concurso: Optional[int] = None) -> Dict[str, Any]:
    """Função para usar no seu endpoint existente"""
    try:
        return scraper.get_resultado(loteria, concurso)
    except Exception as e:
        raise Exception(f"Scraping falhou: {e}")
