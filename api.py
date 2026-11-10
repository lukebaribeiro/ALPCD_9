"""
api.py — Comunicação com a API REST wger (https://wger.de/api/v2/).

Este módulo é o ÚNICO sítio do projeto que faz pedidos HTTP.
Os comandos da CLI (fitcli.py) pedem dados através destas funções e nunca
chamam o requests diretamente. Assim, as boas práticas pedidas no enunciado
(User-Agent, verificação do status code e paginação) ficam implementadas
uma só vez.
"""

import requests

BASE_URL = "https://wger.de/api/v2/"

# Cabeçalho identificativo: diz ao servidor quem está a fazer os pedidos.
HEADERS = {"User-Agent": "fitcli/1.0 (ALPCD 2026/27 - Universidade do Minho - Grupo 9)"}

TIMEOUT = 15        # segundos até desistir de um pedido (evita o programa "pendurado")
PAGE_SIZE = 100     # registos por página pedidos à API
ENGLISH = 2         # id da língua inglesa na wger (parâmetro language=2)


class APIError(Exception):
    """Erro ao comunicar com a API (sem ligação, 404, 500, ...)."""


def get_json(endpoint, params=None):
    """Faz um pedido GET e devolve a resposta já convertida de JSON para Python.

    Args:
        endpoint: caminho relativo (ex.: "exerciseinfo/") ou URL completo
                  (útil para seguir o campo "next" da paginação).
        params: dicionário com os parâmetros do URL (?chave=valor).

    Returns:
        dict com o conteúdo da resposta.

    Raises:
        APIError: se não houver ligação ou o status code não for 200.
    """
    url = endpoint if endpoint.startswith("http") else BASE_URL + endpoint
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
    except requests.RequestException as erro:
        raise APIError(f"Não foi possível ligar à API: {erro}") from erro

    # Verificação do status code (boa prática pedida no enunciado)
    if resp.status_code == 404:
        raise APIError(f"Recurso não encontrado (404): {resp.url}")
    if resp.status_code != 200:
        raise APIError(f"A API respondeu com erro {resp.status_code}: {resp.url}")

    return resp.json()


def get_all(endpoint, params=None, max_results=None):
    """Obtém TODOS os registos de uma rota paginada, seguindo o campo "next".

    A wger devolve os dados em páginas com o formato:
        {"count": 966, "next": "<url da página seguinte>", "previous": ..., "results": [...]}
    Enquanto "next" não for None, ainda há mais páginas para pedir.

    Args:
        endpoint: rota da API (ex.: "exerciseinfo/").
        params: filtros a aplicar (ex.: {"category": 11}).
        max_results: se indicado, pára assim que tiver esse número de registos
                     (evita descarregar a base de dados inteira sem necessidade).

    Returns:
        lista com os registos (dicts).
    """
    params = dict(params or {})          # cópia, para não alterar o dict de quem chamou
    # Se só queremos poucos registos (ex.: top 5), não vale a pena pedir 100
    tamanho = min(PAGE_SIZE, max_results) if max_results else PAGE_SIZE
    params.setdefault("limit", tamanho)

    resultados = []
    pagina = get_json(endpoint, params)
    while True:
        resultados.extend(pagina["results"])
        if max_results is not None and len(resultados) >= max_results:
            return resultados[:max_results]
        if not pagina["next"]:           # última página
            return resultados
        # O URL em "next" já inclui todos os parâmetros (filtros, limit, offset)
        pagina = get_json(pagina["next"])


def get_exercises(filtros=None, max_results=None):
    """Devolve exercícios completos (rota /exerciseinfo/) em inglês.

    Usamos /exerciseinfo/ em vez de /exercise/ porque já traz a categoria,
    os músculos, o equipamento e as traduções (nome + descrição) num só pedido.
    """
    params = {"language": ENGLISH}
    params.update(filtros or {})
    return get_all("exerciseinfo/", params, max_results)


def get_exercise(exercise_id):
    """Devolve um único exercício pelo seu id (levanta APIError se não existir)."""
    return get_json(f"exerciseinfo/{exercise_id}/")
