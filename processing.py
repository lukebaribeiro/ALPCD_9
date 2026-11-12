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
        # nome comum do músculo (ex.: "Biceps"); se não existir, o nome em latim
        "muscles": [m["name_en"] or m["name"] for m in exercise.get("muscles", [])],
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


# ---------------------------------------------------------------------------
# Alínea c) — tipo de esforço (compound / isolated / cardio / other)
# ---------------------------------------------------------------------------
# A API não tem um campo com o tipo de esforço: inferimo-lo a partir do NOME,
# da CATEGORIA, da DESCRIÇÃO e dos MÚSCULOS. As palavras-chave foram escolhidas
# depois de analisar os 967 exercícios da wger.
#
#   compound (composto)  = movimento com várias articulações e vários músculos
#   isolated (isolado)   = movimento de uma só articulação, foca um músculo
#   cardio               = esforço cardiovascular (correr, saltar, pedalar...)
#   other                = posições estáticas, alongamentos, ou sem informação

# Palavras no NOME que indicam cardio
CARDIO_RE = re.compile(
    r"\b(?:run(?:ning)?|jog(?:ging)?|sprints?|sprinting|cycling|bike|biking|treadmill"
    r"|elliptical|jump(?:ing)?[\s-]?rope|skipping|burpees?|jumping[\s-]?jacks?"
    r"|swim(?:ming)?|rowing machine|stair[\s-]?climb\w*)\b",
    re.IGNORECASE)

# Movimentos compostos. "\w*press" também apanha nomes colados ("Benchpress").
COMPOUND_RE = re.compile(
    r"\b(?:squats?|deadlifts?|\w*press(?:es)?|rows?|rowing|pull[\s-]?ups?|chin[\s-]?ups?"
    r"|dips?|lunges?|cleans?|snatch(?:es)?|thrusters?|push[\s-]?ups?|step[\s-]?ups?|jerks?"
    r"|good[\s-]?mornings?|swings?|hip[\s-]?thrusts?|pull[\s-]?downs?|high[\s-]?pulls?)\b",
    re.IGNORECASE)

# Movimentos isolados. "\w*curls?" também apanha "Hammercurls".
ISOLATED_RE = re.compile(
    r"\b(?:\w*curls?|raises?|fl(?:y|ye|yes|ies)|butterfly|extensions?|kick[\s-]?backs?"
    r"|crunch(?:es)?|shrugs?|pec[\s-]?deck|pullovers?|sit[\s-]?ups?|planks?|twists?"
    r"|bridges?|push[\s-]?downs?|cross[\s-]?overs?)\b",
    re.IGNORECASE)

# Exercícios estáticos / alongamentos -> other
OTHER_RE = re.compile(
    r"\b(?:stretch\w*|holds?|isometric|mobility|foam[\s-]?roll\w*|hang(?:s|ing)?)\b",
    re.IGNORECASE)

# Frases explícitas na DESCRIÇÃO
DESC_COMPOUND_RE = re.compile(r"\b(?:compound|multi[\s-]?joint)\b", re.IGNORECASE)
DESC_ISOLATED_RE = re.compile(r"\b(?:isolat\w*|single[\s-]joint)\b", re.IGNORECASE)


def effort_with_reason(exercise):
    """Classifica o tipo de esforço e devolve também o motivo da decisão.

    As regras são aplicadas por ordem; a primeira que se verificar decide:
      1. categoria "Cardio" ou palavra de cardio no nome     -> cardio
      2. palavra de movimento composto no nome               -> compound
      3. palavra de movimento isolado no nome                -> isolated
      4. palavra de exercício estático/alongamento no nome   -> other
      5. a descrição diz "compound"/"multi-joint"            -> compound
      6. a descrição diz "isolation"/"single-joint"          -> isolated
      7. 2+ músculos principais, ou 3+ no total              -> compound
      8. 1 músculo principal e nenhum secundário             -> isolated
      9. caso contrário                                      -> other

    >>> ex = {"category": {"name": "Chest"}, "muscles": [{}], "muscles_secondary": [{}, {}],
    ...       "translations": [{"language": 2, "name": "Bench Press", "description": ""}]}
    >>> effort_with_reason(ex)
    ('compound', "o nome contém 'Press'")
    """
    traducao = english_translation(exercise)
    nome = traducao.get("name", "")
    descricao = clean_html(traducao.get("description", ""))
    categoria = exercise.get("category", {}).get("name", "")
    n_principais = len(exercise.get("muscles", []))
    n_total = n_principais + len(exercise.get("muscles_secondary", []))

    if categoria == "Cardio":
        return "cardio", "a categoria é Cardio"
    m = CARDIO_RE.search(nome)
    if m:
        return "cardio", f"o nome contém '{m.group()}'"
    m = COMPOUND_RE.search(nome)
    if m:
        return "compound", f"o nome contém '{m.group()}'"
    m = ISOLATED_RE.search(nome)
    if m:
        return "isolated", f"o nome contém '{m.group()}'"
    m = OTHER_RE.search(nome)
    if m:
        return "other", f"o nome contém '{m.group()}'"
    m = DESC_COMPOUND_RE.search(descricao)
    if m:
        return "compound", f"a descrição diz '{m.group()}'"
    m = DESC_ISOLATED_RE.search(descricao)
    if m:
        return "isolated", f"a descrição diz '{m.group()}'"
    if n_principais >= 2 or n_total >= 3:
        return "compound", f"trabalha {n_principais} músculo(s) principal(is) e {n_total} no total"
    if n_principais == 1 and n_total == 1:
        return "isolated", "trabalha um só músculo"
    return "other", "sem informação suficiente para classificar"


def classify_effort(exercise):
    """c) Devolve só o tipo de esforço: "compound", "isolated", "cardio" ou "other"."""
    tipo, _motivo = effort_with_reason(exercise)
    return tipo
