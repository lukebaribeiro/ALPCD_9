"""
processing.py — Transformação e limpeza dos dados vindos da API.

Aqui ficam as funções que NÃO fazem pedidos: recebem dicionários da API e
devolvem estruturas simplificadas. Mais tarde, nas alíneas c) e d), é também
aqui que ficam as expressões regulares (módulo re).
"""

import re

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


def clean_html(texto):
    """Remove as tags HTML de um texto e normaliza os espaços.

    As descrições da wger vêm em HTML (<p>, <ol>, <li>...). Antes de
    procurarmos palavras com regex, tiramos as tags.

    >>> clean_html("<ol>\\n<li>Hold the bar.</li><li>Lower it.</li></ol>")
    'Hold the bar. Lower it.'
    >>> clean_html("")
    ''
    """
    if not texto:                              # descrição vazia ou None
        return ""
    texto = re.sub(r"<[^>]+>", " ", texto)     # 1. cada tag <...> passa a espaço
    texto = re.sub(r"\s+", " ", texto)         # 2. vários espaços seguidos passam a um só
    return texto.strip()                       # 3. tira os espaços do início e do fim


# ---------------------------------------------------------------------------
# Alínea d) — contagem de equipamento nas descrições
# ---------------------------------------------------------------------------

# Cada equipamento -> regex que o reconhece (sem \b; as fronteiras são postas abaixo).
EQUIPMENT_PATTERNS = {
    # "bar" sozinho também conta como barbell, EXCETO depois de pull-up / chin-up / sz / ez
    "barbell": r"barbells?|(?<!pull-up )(?<!pullup )(?<!pull up )(?<!chin-up )"
               r"(?<!sz-)(?<!sz )(?<!ez-)(?<!ez )bars?",
    "dumbbell": r"dumbbells?",
    "cable": r"cables?",
    "machine": r"machines?",
    "bodyweight": r"body[\s-]?weight",          # bodyweight, body weight, body-weight
    "bench": r"bench(?:es)?",
    "kettlebell": r"kettlebells?",
    "resistance band": r"(?:resistance )?bands?",
    "pull-up bar": r"(?:pull|chin)[\s-]?up bars?",
    "ez-bar": r"(?:ez|sz)[\s-]bars?",
}

# Compilamos cada regex UMA vez, já com \b à volta e a ignorar maiúsculas.
# (?:...) é um grupo SEM captura: agrupa as alternativas sem alterar o que o findall devolve.
EQUIPMENT_REGEX = {
    nome: re.compile(rf"\b(?:{padrao})\b", re.IGNORECASE)
    for nome, padrao in EQUIPMENT_PATTERNS.items()
}


def count_equipment(exercises):
    """d) Conta as menções a cada equipamento nas descrições dos exercícios.

    Devolve uma lista ordenada por ordem decrescente de ocorrências, no
    formato do enunciado: [{"bench": 38}, {"dumbbell": 25}, ...].
    Equipamentos com 0 menções não aparecem.

    >>> ex = {"translations": [{"language": 2,
    ...       "description": "<p>Lie on the bench and hold the bar.</p><p>Use a bench.</p>"}]}
    >>> count_equipment([ex])
    [{'bench': 2}, {'barbell': 1}]
    """
    contagem = {nome: 0 for nome in EQUIPMENT_REGEX}
    for exercise in exercises:
        descricao = english_translation(exercise).get("description", "")
        texto = clean_html(descricao)
        for nome, regex in EQUIPMENT_REGEX.items():
            contagem[nome] += len(regex.findall(texto))

    # Ordena por contagem (decrescente); em caso de empate, por ordem alfabética
    ordenado = sorted(contagem.items(), key=lambda par: (-par[1], par[0]))
    return [{nome: total} for nome, total in ordenado if total > 0]
