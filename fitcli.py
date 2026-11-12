"""
fitcli.py — Command Line Interface para explorar a API wger.

Utilização:
    python fitcli.py --help
    python fitcli.py top 10
"""

import json
from typing import Optional

import typer

import api
import processing

app = typer.Typer(help="CLI para pesquisar exercícios físicos na API wger.")


@app.callback()
def main():
    """CLI para pesquisar exercícios físicos na API wger."""
    # Com um só comando, o typer trata-o como "comando por defeito" e deixaria
    # de aceitar "python fitcli.py top 10". Este callback obriga o typer a
    # funcionar sempre com subcomandos (top, search, type, ...).


def print_json(dados):
    """Escreve qualquer estrutura Python no terminal em formato JSON legível."""
    typer.echo(json.dumps(dados, indent=2, ensure_ascii=False))


@app.command()
def top(n: int = typer.Argument(..., min=1, help="Número de exercícios a mostrar")):
    """a) Lista os N exercícios mais recentes (nome, categoria e equipamento)."""
    try:
        # ordering=-created -> ordenar por data de criação, do mais recente para o mais antigo
        exercicios = api.get_exercises({"ordering": "-created"}, max_results=n)
    except api.APIError as erro:
        typer.echo(f"Erro: {erro}", err=True)
        raise typer.Exit(code=1)

    print_json([processing.summarize(ex) for ex in exercicios])



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


if __name__ == "__main__":
    app()
