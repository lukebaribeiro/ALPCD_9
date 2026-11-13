"""
api.py — Comunicação com a API REST wger (https://wger.de/api/v2/).

Este módulo é o ÚNICO sítio do projeto que faz pedidos HTTP.
Os comandos da CLI (fitcli.py) pedem dados através destas funções e nunca
chamam o requests diretamente. Assim, as boas práticas pedidas no enunciado
(User-Agent, verificação do status code e paginação) ficam implementadas
uma só vez.
"""

from functools import lru_cache

import requests

BASE_URL = "https://wger.de/api/v2/"

# Cabeçalho identificativo: diz ao servidor quem está a fazer os pedidos.
HEADERS = {"User-Agent": "fitcli/1.0 (ALPCD 2026/27 - Universidade do Minho - Grupo 9)"}

TIMEOUT = 15        # segundos até desistir de um pedido (evita o programa "pendurado")
PAGE_SIZE = 100     # registos por página pedidos à API
ENGLISH = 2         # id da língua inglesa na wger (parâmetro language=2)


class APIError(Exception):
    """Erro ao comunicar com a API (sem ligação, 404, 500, ...)."""


class NotFoundError(APIError):
    """O recurso pedido não existe (status 404).

    É uma subclasse de APIError (herança): quem apanha APIError também a
    apanha, mas quem quiser pode tratar o "não existe" de forma diferente.
    """


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
        raise NotFoundError(f"Recurso não encontrado (404): {resp.url}")
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


# @lru_cache guarda o resultado da primeira chamada: as categorias e os músculos
# quase nunca mudam, por isso no comando workout ("biceps,back,chest") pedimo-los
# à API uma só vez em vez de uma vez por grupo.
@lru_cache(maxsize=None)
def get_categories():
    """Lista das categorias de exercícios (Abs, Arms, Back, Chest, ...)."""
    return get_all("exercisecategory/")


@lru_cache(maxsize=None)
def get_muscles():
    """Lista dos músculos. Cada um tem "name" (latim) e "name_en" (nome comum)."""
    return get_all("muscle/")


def resolve_filter(termo):
    """Converte o nome de um músculo ou categoria no filtro da API.

    Exemplos:
        resolve_filter("chest")   -> {"category": 11}
        resolve_filter("biceps")  -> {"muscles": 1}
        resolve_filter("xpto")    -> levanta APIError

    Ordem de procura (ignora maiúsculas e espaços a mais):
      1. nome de uma CATEGORIA          ("Chest", "Back", ...)
      2. nome comum de um MÚSCULO       ("Biceps", "Lats", ...)
      3. nome em latim de um MÚSCULO    ("Biceps brachii", ...)
      4. parte do nome de UM só músculo ("pectoralis" -> "Pectoralis major")
    As categorias vêm primeiro porque alguns nomes existem nas duas listas
    (ex.: "Chest" é categoria e é o nome comum do Pectoralis major).
    """
    alvo = termo.strip().lower()
    categorias = get_categories()
    musculos = get_muscles()

    # 1. Categoria com o nome exato
    for categoria in categorias:
        if categoria["name"].lower() == alvo:
            return {"category": categoria["id"]}

    # 2 e 3. Músculo com o nome comum ou o nome em latim exato
    for musculo in musculos:
        if alvo in (musculo["name_en"].lower(), musculo["name"].lower()):
            return {"muscles": musculo["id"]}

    # 4. Músculo cujo nome em latim CONTÉM o termo, desde que seja só um
    parecidos = [m for m in musculos if alvo in m["name"].lower()]
    if len(parecidos) == 1:
        return {"muscles": parecidos[0]["id"]}

    # Nada encontrado (ou ambíguo): mensagem com as opções válidas
    opcoes = sorted({c["name"] for c in categorias}
                    | {m["name_en"] or m["name"] for m in musculos})
    raise APIError(f"Músculo/categoria desconhecido: '{termo}'. "
                   f"Opções válidas: {', '.join(opcoes)}")
