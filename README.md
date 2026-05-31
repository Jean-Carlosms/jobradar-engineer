# JobRadar Engineer

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/Tests-passing-brightgreen)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-red)
![SQLite](https://img.shields.io/badge/SQLite-local-lightgrey)
![Status](https://img.shields.io/badge/Status-portfolio--ready-success)

## Visao geral

JobRadar Engineer e um robo local em Python para buscar, pontuar, analisar e visualizar vagas publicas aderentes a um perfil de engenharia mecatronica, automacao industrial, dados industriais, Python, Power BI, CLP/PLC, robotica e Industria 4.0.

O projeto foi preparado para uso local e apresentacao em portfolio, com dados ficticios, dashboard Streamlit, testes automatizados e cuidados para nao versionar informacoes sensiveis.

## Problema

Buscar vagas compativeis com um perfil tecnico exige consultar varias fontes, filtrar resultados pouco aderentes, comparar requisitos e lembrar quais vagas ja foram enviadas ou analisadas.

## Solucao

O sistema coleta vagas publicas, calcula score explicavel, remove duplicatas, salva em SQLite, gera analise vaga x perfil, envia relatorios por e-mail e exibe tudo em um dashboard local.

## Funcionalidades

- Fonte mock e busca publica por mecanismo de pesquisa.
- Perfil profissional configuravel por YAML.
- Score de aderencia com justificativa.
- Deduplicacao por URL e por titulo + empresa + local.
- Persistencia em SQLite.
- Analise vaga x perfil/curriculo baseada em regras locais.
- E-mail com melhores vagas e resumo de analise.
- Dashboard Streamlit com filtros, graficos e exportacao CSV.
- Scripts Windows para dry-run, producao e dashboard.
- Banco ficticio para screenshots e portfolio.

## Arquitetura

```text
config/                 perfis YAML
src/sources/            fontes de vagas
src/services/           scoring, e-mail, scheduler e analise
src/models/             modelos SQLAlchemy
src/database.py         repositorio SQLite
dashboard.py            dashboard Streamlit
scripts/                automacao Windows e sample data
examples/               dados ficticios
docs/                   guias de operacao e portfolio
tests/                  testes automatizados
```

## Tecnologias

Python, Requests, BeautifulSoup, SQLAlchemy, SQLite, PyYAML, Pandas, Streamlit, APScheduler, pytest e scripts Windows `.bat`.

## Como rodar

Instale as dependencias:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Configure o ambiente:

```bat
copy .env.example .env
```

Rodar coleta simulada com analise e sem envio real:

```bat
python -m src.main --source mock --analyze --dry-run --min-score 50 --analysis-min-score 50
```

Rodar busca completa com e-mail real, dependendo do `.env`:

```bat
python -m src.main --source all --analyze --send-email --min-score 50 --analysis-min-score 50
```

## Como rodar com dados de exemplo

Os dados de exemplo sao ficticios e seguros para portfolio.

```bat
python scripts\load_sample_data.py
```

Isso cria:

```text
data/sample_jobs.db
```

Esse banco nao sobrescreve `data/jobs.db`.

## Dashboard

Abrir dashboard:

```bat
streamlit run dashboard.py
```

Ou:

```bat
scripts\open_dashboard.bat
```

No dashboard, use o seletor lateral `Banco de dados`:

- `Real local`: usa `data/jobs.db`.
- `Dados ficticios`: usa `data/sample_jobs.db`.

Tambem e possivel definir:

```bat
set JOBRADAR_DASHBOARD_DB=data\sample_jobs.db
streamlit run dashboard.py
```

## Agendamento no Windows

Teste controlado sem envio real:

```bat
scripts\run_jobradar_dry_run.bat
```

Execucao diaria com busca publica, analise e envio real por SMTP:

```bat
scripts\run_jobradar_daily.bat
```

Documentacao:

- `docs/windows_task_scheduler.md`
- `docs/production_setup.md`

## Seguranca e compliance

- Nao automatiza login.
- Nao automatiza candidatura.
- Nao burla captcha.
- Nao ignora bloqueios de acesso.
- Usa apenas dados publicos de vagas.
- Nao coleta dados sensiveis.
- `.env`, `.venv/`, `logs/` e `data/jobs.db` nao devem ser versionados.
- Prints publicos devem usar dados ficticios ou sanitizados.

Veja tambem:

- `SECURITY.md`
- `docs/SCREENSHOTS_GUIDE.md`

## Limitacoes

- A busca publica depende de resultados de mecanismo de pesquisa.
- Snippets podem ser incompletos e afetar score/analise.
- A analise vaga x perfil e baseada em regras locais, sem IA externa.
- O dashboard nao coleta dados sozinho; ele apenas le SQLite.
- Envio real depende do SMTP configurado no `.env`.

## Roadmap

- Melhorar fontes com APIs publicas oficiais.
- Adicionar cache de consultas.
- Exportar Excel.
- Criar favoritos, bloqueios e detalhes da vaga.
- Adicionar CI real no GitHub Actions.

## Screenshots futuros

Os prints devem ser feitos com `data/sample_jobs.db` ou dados sanitizados:

- dashboard principal;
- filtros laterais;
- tabela de vagas;
- Top Vagas;
- Empresas Prioritarias;
- Analise Vaga x Perfil;
- graficos;
- e-mail dry-run sanitizado;
- logs sanitizados.

Guia completo: `docs/SCREENSHOTS_GUIDE.md`.

## Publicacao e Portfolio

Materiais de apoio para publicar o projeto com seguranca:

- `PORTFOLIO_SUMMARY.md`: resumo do projeto para portfolio.
- `docs/PUBLISHING_CHECKLIST.md`: checklist final antes de publicar.
- `docs/GITHUB_DESCRIPTION.md`: texto curto e tags para o campo About do GitHub.
- `docs/LINKEDIN_POST.md`: rascunho de post profissional para LinkedIn.
- `docs/INTERVIEW_PITCH.md`: pitch de entrevista e explicacao tecnica.

Antes de publicar, rode:

```bat
python scripts\check_publication_safety.py
python -m pytest
```

## Status do projeto

Versao atual: `v0.7.0 - Release e publicacao segura`.

Testes:

```bat
python -m pytest
```
