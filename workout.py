"""
workout.py — Alínea e): gera um plano de treino personalizado.

Não tem lógica nova de pesquisa nem de classificação: COMPÕE as funções das
alíneas anteriores (resolve_filter + get_exercises da b, classify_effort da c).
"""

import re

import api
import processing

TIPOS_VALIDOS = ("compound", "isolated", "any")


def parse_groups(texto):
    """Separa "biceps, back,chest" em ["biceps", "back", "chest"] (sem repetidos).

    >>> parse_groups("biceps, back ,chest,biceps")
    ['biceps', 'back', 'chest']
    """
    grupos = []
    for parte in re.split(r"\s*,\s*", texto.strip()):   # vírgula com ou sem espaços
        if parte and parte.lower() not in grupos:
            grupos.append(parte.lower())
    return grupos


def build_plan(grupos, tipo, n):
    """Constrói o plano: para cada músculo/categoria, até N exercícios do tipo pedido.

    Args:
        grupos: lista de nomes, ex.: ["biceps", "back"].
        tipo: "compound", "isolated" ou "any" (sem filtro).
        n: número máximo de exercícios por grupo.

    Returns:
        dict {grupo: [ {id, name, type, category, equipment}, ... ]}

    Raises:
        api.APIError: se um nome não existir ou a API falhar.
        ValueError: se o tipo não for válido.
    """
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: '{tipo}'. Use: {', '.join(TIPOS_VALIDOS)}")

    plano = {}
    for grupo in grupos:
        filtro = api.resolve_filter(grupo)              # alínea b)
        escolhidos = []
        for exercicio in api.get_exercises(filtro):     # todos os do grupo (paginação)
            esforco = processing.classify_effort(exercicio)   # alínea c)
            if tipo == "any" or esforco == tipo:
                resumo = processing.summarize(exercicio)
                escolhidos.append({
                    "id": resumo["id"],
                    "name": resumo["name"],
                    "type": esforco,
                    "category": resumo["category"],
                    "equipment": resumo["equipment"],
                })
            if len(escolhidos) == n:                    # já temos N: passa ao grupo seguinte
                break
        plano[grupo] = escolhidos
    return plano
