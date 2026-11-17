"""
fitcli.py — Command Line Interface para explorar a API wger.

Utilização:
    python fitcli.py --help
    python fitcli.py <comando> --help
"""

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


# =============================================================================
# c) type — Lucas
# =============================================================================


# =============================================================================
# d) equipment — Lucas
# =============================================================================


# =============================================================================
# e) workout — Bruna
# =============================================================================


if __name__ == "__main__":
    app()
