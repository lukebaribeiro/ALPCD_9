"""
fitcli.py — Command Line Interface para explorar a API wger.

Utilização:
    python fitcli.py --help
    python fitcli.py <comando> --help
"""
import re

import json
from typing import Optional

import typer

import api
import processing
# Bruna: acrescentar aqui "import export" e "import workout as plano_treino"

app = typer.Typer(help="CLI para pesquisar exercícios físicos na API wger.")


@app.callback()
def main():
    """CLI para pesquisar exercícios físicos na API wger."""
    # Com um só comando, o typer trata-o como "comando por defeito" e deixaria
    # de aceitar "python fitcli.py top 10". Este callback obriga o typer a
    # funcionar sempre com subcomandos (top, search, type, ...).


def print_json(dados):
    """Escreve qualquer estrutura Python no terminal em formato JSON legível."""
    typer.echo(json.dumps(dados, indent=4, ensure_ascii=False))


def erro_e_sair(mensagem):
    """Mostra uma mensagem de erro (no stderr) e termina com código 1."""
    typer.echo(f"Erro: {mensagem}", err=True)
    raise typer.Exit(code=1)


# =============================================================================
# a) top — Lucas
# =============================================================================

@app.command()
def top(n: int = typer.Argument(..., min=1, help="Número de exercícios a mostrar")):
    """a) Lista os N exercícios mais recentes (nome, categoria e equipamento)."""
    try:
        # ordering=-created -> ordenar por data de criação, do mais recente para o mais antigo
        exercicios = api.get_exercises({"ordering": "-created"}, max_results=n)
    except api.APIError as erro:
        erro_e_sair(erro)

    print_json([processing.summarize(ex) for ex in exercicios])


# =============================================================================
# b) search — Francisca
# =============================================================================
@app.command()
def search(
    termo: str = typer.Argument(..., help="Músculo ou categoria (ex.: biceps, chest)"),
    n: int = typer.Argument(..., min=1, help="Número máximo de resultados"),
    categoria: Optional[str] = typer.Option(
        None, "--categoria", "-c",
        help="Categoria a combinar com um músculo (ex.: search biceps 5 --categoria arms)"),
):
    """b) Pesquisa exercícios por músculo e/ou categoria (até N resultados)."""
    try:
        filtro = api.resolve_filter(termo)             # "biceps" -> {"muscles": 1}
        if categoria:                                  # "e": juntar uma categoria ao músculo
            extra = api.resolve_filter(categoria)
            if "category" not in extra:
                raise api.APIError(f"'{categoria}' não é uma categoria.")
            if "category" in filtro:
                raise api.APIError("Para combinar, o termo tem de ser um músculo e --categoria uma categoria.")
            filtro.update(extra)                       # {"muscles": 1, "category": 8}
        exercicios = api.get_exercises(filtro, max_results=n)
    except api.APIError as erro:
        typer.echo(f"Erro: {erro}", err=True)
        raise typer.Exit(code=1)

    print_json([processing.summarize(ex) for ex in exercicios])

# =============================================================================
# c) type — Bruna
# =============================================================================
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
        descricao = processing.english_translation(exercise).get("description", "")
        texto = processing.clean_html(descricao)
        for nome, regex in EQUIPMENT_REGEX.items():
            contagem[nome] += len(regex.findall(texto))

    # Ordena por contagem (decrescente); em caso de empate, por ordem alfabética
    ordenado = sorted(contagem.items(), key=lambda par: (-par[1], par[0]))
    return [{nome: total} for nome, total in ordenado if total > 0]

# =============================================================================
# d) equipment — Lucas
# =============================================================================
@app.command()
def equipment(categoria: str = typer.Argument(..., help="Categoria (ex.: chest, back, legs)")):
    """d) Conta as menções a equipamento nas descrições de uma categoria."""
    try:
        filtro = api.resolve_filter(categoria)        # "chest" -> {"category": 11}
        exercicios = api.get_exercises(filtro)        # todos os exercícios (com paginação)
    except api.APIError as erro:
        typer.echo(f"Erro: {erro}", err=True)
        raise typer.Exit(code=1)

    print_json(processing.count_equipment(exercicios))

# =============================================================================
# e) workout — Bruna
# =============================================================================


if __name__ == "__main__":
    app()
