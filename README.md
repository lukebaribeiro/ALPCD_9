# ALPCD_9 — fitcli

CLI (Command Line Interface) em Python para pesquisar e analisar dados de exercício físico
da API pública [wger](https://wger.de/api/v2/).

Trabalho Prático — Parte 1 de **Ambientes e Linguagens de Programação para Ciência de Dados (ALPCD)**,
Licenciatura em Ciência de Dados, Universidade do Minho, 2026/27.

## Grupo 9

| Nome | Número |
|---|---|
| _Lucas Ribeiro_ | A116109 |
| _Bruna Castro_ | A113856 |
| _Francisca Marques_ | A114880 |

## Instalação (Windows)

```powershell
git clone https://github.com/lukebaribeiro/ALPCD_9.git
cd ALPCD_9
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Comandos

| Comando | Descrição | Exemplo |
|---|---|---|
| `top` | N exercícios mais recentes | `python fitcli.py top 10` |
| `search` | Exercícios por músculo/categoria | `python fitcli.py search biceps 5` |
| `type` | Tipo de esforço de um exercício | `python fitcli.py type <exercise_id>` |
| `equipment` | Menções a equipamento numa categoria | `python fitcli.py equipment chest` |
| `workout` | Plano de treino personalizado (+ CSV) | `python fitcli.py workout biceps,back compound 5 --csv treino.csv` |

_(em desenvolvimento)_
