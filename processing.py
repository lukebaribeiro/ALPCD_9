"""
processing.py — Transformação e limpeza dos dados vindos da API.

Aqui ficam as funções que NÃO fazem pedidos: recebem dicionários da API e
devolvem estruturas simplificadas. As expressões regulares (módulo re) das
alíneas c) e d) também ficam aqui.
"""

import re

ENGLISH = 2


def english_translation(exercise):
    """Devolve a tradução inglesa de um exercício (dict com "name" e "description").

    Na wger, o nome e a descrição estão dentro da lista "translations" (uma
    entrada por língua) e o parâmetro language=2 NÃO filtra essa lista.
    Por isso escolhemos nós a tradução com language == 2. Se não existir,
    usamos a primeira disponível; se não houver nenhuma, devolvemos {}.

    >>> english_translation({"translations": [{"language": 7, "name": "Supino"},
    ...                                       {"language": 2, "name": "Bench Press"}]})["name"]
    'Bench Press'
    >>> english_translation({"translations": []})
    {}
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
         "muscles": [m["name_en"] or m["name"] for m in exercise.get("muscles", [])],
    }


# =============================================================================
# Lucas — clean_html, EQUIPMENT_PATTERNS e count_equipment (alínea d)
# =============================================================================


# =============================================================================
# Lucas — effort_with_reason e classify_effort (alínea c)
# =============================================================================
