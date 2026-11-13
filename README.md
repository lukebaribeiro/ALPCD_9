# ALPCD_9 — fitcli

CLI (*Command Line Interface*) em Python que obtém dados de exercício físico da API pública
[wger](https://wger.de/api/v2/) e os transforma em informação útil: pesquisar exercícios,
classificar o tipo de esforço, contar o equipamento mencionado e gerar planos de treino em CSV.

Trabalho Prático — Parte 1 de **Ambientes e Linguagens de Programação para Ciência de Dados (ALPCD)**,
Licenciatura em Ciência de Dados, Universidade do Minho, 2026/27.

## Grupo 9

| Nome | Número |
|---|---|
| Lucas Ribeiro | A116109 |
| Bruna Castro | A113856 |
| Francisca Marques | A114880 |

## Instalação

Requisitos: **Python 3.10 ou superior**, **git** e ligação à internet.
Bibliotecas (instaladas pelo `requirements.txt`): `requests` e `typer`.

### Windows (PowerShell)

```powershell
git clone https://github.com/lukebaribeiro/ALPCD_9.git
cd ALPCD_9
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python fitcli.py --help
```

Se o PowerShell disser que a execução de scripts está desativada, correr uma vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e ativar o ambiente de novo.

### macOS e Linux (Terminal)

```bash
git clone https://github.com/lukebaribeiro/ALPCD_9.git
cd ALPCD_9
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python fitcli.py --help
```

Em algumas distribuições Linux (ex.: Ubuntu/Debian) é preciso instalar primeiro o módulo
de ambientes virtuais: `sudo apt install python3-venv`.

Com o ambiente ativo, o terminal mostra `(.venv)` no início da linha. Para o desativar: `deactivate`.

## Comandos

### a) `top N` — exercícios mais recentes

```
python fitcli.py top 3
```
Devolve em JSON os N exercícios mais recentes (pedido com `ordering=-created`), com nome,
categoria, equipamento e músculos.

### b) `search TERMO N [--categoria CAT]` — pesquisa por músculo e/ou categoria

```
python fitcli.py search biceps 5
python fitcli.py search biceps 3 --categoria arms
```
`TERMO` pode ser um músculo (`biceps`, `lats`, `trapezius`) ou uma categoria (`chest`, `back`).
Com `--categoria`, combina um músculo **e** uma categoria. Exemplo: `search biceps 5` inclui
"Chin Up" (categoria Back); com `--categoria arms` só aparecem exercícios de Arms.

### c) `type ID [--motivo]` — tipo de esforço

```
python fitcli.py type 73              # compound
python fitcli.py type 73 --motivo     # compound (o nome contém 'Press')
python fitcli.py type 192             # Erro: não existe nenhum exercício com o id 192.
```
Classifica o exercício em `compound`, `isolated`, `cardio` ou `other` (regras abaixo).
Nota: o id 192 do exemplo do enunciado já não existe na API.

### d) `equipment CATEGORIA` — equipamento mencionado nas descrições

```
python fitcli.py equipment chest
# resultado (resumido numa linha):
[{"bench": 38}, {"dumbbell": 25}, {"barbell": 20}, {"cable": 20}, {"machine": 12}, {"bodyweight": 5}]
```
Conta com expressões regulares as menções a equipamento nas descrições da categoria,
por ordem decrescente.

### e) `workout GRUPOS TIPO N [--csv FICHEIRO]` — plano de treino

```
python fitcli.py workout biceps,back compound 5
python fitcli.py workout chest,shoulders isolated 3 --csv treino.csv
Ficheiro exportado: treino.csv (6 registos)
```
`GRUPOS` são músculos/categorias separados por vírgula (sem espaços, ou entre aspas);
`TIPO` é `compound`, `isolated` ou `any`. O CSV tem as colunas
`group, id, name, type, category, equipment` (equipamento separado por `; `).

## Estrutura

| Ficheiro | Responsabilidade |
|---|---|
| `fitcli.py` | Comandos da CLI (typer): valida argumentos, trata erros e escreve o output |
| `api.py` | Único módulo que faz pedidos HTTP: User-Agent, timeout, verificação do status code, paginação, `resolve_filter` |
| `processing.py` | Transformação dos dados, sem pedidos: tradução inglesa, resumo, limpeza de HTML, regex de equipamento e de tipo de esforço |
| `workout.py` | Composição das alíneas b) e c) para gerar o plano |
| `export.py` | Exportação do plano para CSV |

```
fitcli.py ──> api.py ──GET──> API wger (JSON)
    │
    ├──> processing.py   (limpeza e regex)
    └──> workout.py ──> api.py + processing.py ──> export.py (CSV)
```

## Boas práticas de utilização da API

- **User-Agent** identificativo em todos os pedidos (`fitcli/1.0 (ALPCD 2026/27 - Universidade do Minho - Grupo 9)`).
- **Status code** verificado em cada resposta: 404 dá `NotFoundError`, outros erros dão `APIError`, sempre com mensagem clara.
- **Paginação**: `get_all` segue o campo `next` até à última página, ou pára quando já tem os N registos pedidos.
- **Timeout** de 15 segundos e **cache** (`lru_cache`) das listas de categorias e músculos.

## Decisões de implementação

**Tradução inglesa.** O nome e a descrição estão em `translations`, e o parâmetro `language=2`
não filtra essa lista; escolhemos a tradução com `language == 2`.

**Nome → filtro da API (`resolve_filter`).** Procura, por esta ordem: nome de categoria, nome comum
do músculo, nome em latim, parte do nome em latim. As categorias vêm primeiro porque "Chest" e
"Shoulders" existem nas duas listas. Nomes inexistentes mostram as opções válidas.

**Equipamento (alínea d).** Contamos os 5 equipamentos do enunciado e os restantes definidos pela
API em `/equipment/` (bench, kettlebell, resistance band, pull-up bar, ez-bar). As descrições são
limpas de HTML com `re.sub(r"<[^>]+>", " ", texto)`. Cada equipamento tem a sua regex com `\b`,
plural opcional e sem distinção de maiúsculas. As descrições escrevem muitas vezes "the bar" em vez
de "barbell", por isso "bar" sozinho conta como barbell, exceto depois de "pull-up", "chin-up",
"SZ" ou "EZ" (*lookbehind* negativo). Em `chest`, isto faz o barbell passar de 1 para 20 menções.

**Tipo de esforço (alínea c).** A API não tem este campo; é inferido pela primeira regra que se verificar:

| # | Regra | Tipo |
|---|---|---|
| 1 | categoria Cardio, ou nome com run, cycling, burpees, jumping jacks... | cardio |
| 2 | nome com movimento composto (squat, press, row, lunge, deadlift, pull-up...) | compound |
| 3 | nome com movimento isolado (curl, raise, fly, extension, kickback...) | isolated |
| 4 | nome com exercício estático ou alongamento (stretch, hold, isometric...) | other |
| 5–6 | descrição diz "compound"/"multi-joint" ou "isolation"/"single-joint" | compound / isolated |
| 7 | 2+ músculos principais, ou 3+ no total | compound |
| 8 | um só músculo | isolated |
| 9 | caso contrário | other |

As palavras-chave foram escolhidas depois de analisar os 967 exercícios da API (ex.: `\w*press`
apanha "Benchpress", `\w*curls?` apanha "Hammercurls").

**Plano de treino (alínea e).** `build_plan` não tem lógica própria: para cada grupo usa
`resolve_filter` e `get_exercises` (alínea b) e `classify_effort` (alínea c), até ter N exercícios.
Se um grupo tiver menos de N, mostra um aviso.

## Testes

```powershell
python -m doctest -v processing.py workout.py
```
Os comandos foram também testados com uma API simulada (erros, paginação, ficheiros) e com os
dados reais da wger (categorias chest, back e arms).

## Limitações

- A classificação do tipo de esforço é feita por regras: alguns exercícios ficam mal classificados
  (ex.: "Wall Slides" aparece como compound por trabalhar vários músculos).
- "cable machine" conta como cable e como machine.
- A API não permite filtrar por dois músculos ao mesmo tempo, por isso `search` combina no máximo
  um músculo e uma categoria.
- O programa depende da API wger estar disponível; sem ligação mostra uma mensagem de erro.
