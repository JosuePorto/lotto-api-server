# Adicione este novo endpoint ao seu main.py no GitHub
@app.get("/historico/{modalidade}")
def get_historico_completo(modalidade: str):
    slug = modalidade.lower().replace("-", "")
    # Rota da API comunitária que entrega a lista completa (JSON pesado)
    url = f"https://loteriascaixa-api.herokuapp.com/api/{slug}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Retorna a lista completa de todos os concursos da história
            return response.json() 
        return {"error": "Falha ao buscar histórico"}
    except Exception as e:
        return {"error": str(e)}
