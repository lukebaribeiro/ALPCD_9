"""
processing.py — Transformação e limpeza dos dados vindos da API.

Aqui ficam as funções que NÃO fazem pedidos: recebem dicionários da API e
devolvem estruturas simplificadas. Mais tarde, nas alíneas c) e d), é também
aqui que ficam as expressões regulares (módulo re).
"""

ENGLISH = 2


def english_translation(exercise):
    """Devolve a tradução inglesa de um exercício.

    Na wger, o nome e a descrição estão dentro da lista "translations" (uma
    entrada por língua) e o parâmetro language=2 NÃO filtra essa lista.
    Por isso escolhemos nós a tradução com language == 2. Se não existir,
    usamos a primeira disponível; se não houver nenhuma, devolvemos {}.
    """
    traducoes = exercise.get("translations", [])
    for traducao in traducoes:
        if traducao.get("language") == ENGLISH:
            return traducao
    return traducoes[0] if traducoes else {}


def summarize(exercise):
    """Reduz um exercício da API aos campos que interessam ao utilizador."""
    return {
        "id": exercise["id"],
        "name": english_translation(exercise).get("name", "(sem nome)"),
        "category": exercise["category"]["name"],
        "equipment": [eq["name"] for eq in exercise.get("equipment", [])],
    }
