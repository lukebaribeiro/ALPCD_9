"""
export.py — Exportação do plano de treino para CSV (alínea e).
"""

import csv

COLUNAS = ["group", "id", "name", "type", "category", "equipment"]


def to_csv(plano, caminho):
    """Escreve o plano num ficheiro CSV e devolve o número de registos escritos.

    Uma linha por exercício. A lista de equipamento é guardada numa só
    célula, separada por "; " (ex.: "Barbell; Bench").
    """
    registos = 0
    # newline="" evita linhas em branco a mais no Windows; utf-8 mantém os acentos
    with open(caminho, "w", newline="", encoding="utf-8") as ficheiro:
        writer = csv.DictWriter(ficheiro, fieldnames=COLUNAS)
        writer.writeheader()
        for grupo, exercicios in plano.items():
            for ex in exercicios:
                writer.writerow({
                    "group": grupo,
                    "id": ex["id"],
                    "name": ex["name"],
                    "type": ex["type"],
                    "category": ex["category"],
                    "equipment": "; ".join(ex["equipment"]),
                })
                registos += 1
    return registos
