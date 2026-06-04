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

Rodar fonte publica dedicada da Gupy:

```bat
python -m src.main --source gupy --analyze --dry-run --min-score 50 --analysis-min-score 50
```

Diagnosticar busca publica:

```bat
python -m src.main --source search --debug-search --dry-run --min-score 0 --analysis-min-score 0
```

Com `--debug-search`, o sistema grava amostras sanitizadas em `logs/search_debug/`, incluindo HTML retornado e links extraidos.

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

## Fonte Gupy publica

A fonte dedicada da Gupy reduz a dependencia de buscadores HTML. Configure empresas em:

```text
config/gupy_companies.yaml
```

Formato:

```yaml
categories:
  education_research:
    - name: Facens
      slug: facens
      base_url: https://facens.gupy.io
      priority: true
      status: active
      notes: Board publico validado em execucao anterior.
```

O formato antigo tambem continua aceito:

```yaml
companies:
  - name: Facens
    slug: facens
    base_url: https://facens.gupy.io
```

Campos opcionais por empresa:

- `category`: agrupamento como `education_research`, `industry_manufacturing`, `technology_data`, `energy_infrastructure`, `consulting_engineering` ou `logistics_mobility`.
- `priority`: indica empresas mais relevantes para o perfil ou para vagas tecnicas.
- `status`: status configurado conhecido, como `active`, `invalid_slug` ou `unknown`.
- `notes`: observacoes de curadoria.

O status configurado nao substitui o teste real. A cada execucao, a fonte Gupy consulta as paginas publicas e registra o HTTP recebido. Um `404` pode indicar slug invalido, board inexistente, board privado, redirecionamento nao coberto ou empresa fora da Gupy publica.

Comandos:

```bat
python -m src.main --source gupy --debug-search --dry-run --min-score 0 --analysis-min-score 0
python -m src.main --source all --dry-run --min-score 50 --analysis-min-score 50
python -m src.main --source all --include-mock-in-all --dry-run --min-score 50 --analysis-min-score 50
```

Comportamento das fontes:

- `--source mock`: usa apenas dados ficticios de desenvolvimento.
- `--source gupy`: usa apenas paginas publicas Gupy configuradas.
- `--source search`: usa busca publica via mecanismo de pesquisa.
- `--source all`: usa Gupy publica + BuscaPublica.
- `--include-mock-in-all`: inclui mock tambem em `all`, somente quando solicitado.

Com `--debug-search`, a fonte Gupy salva HTML sanitizado e links extraidos em `logs/gupy_debug/`.

Com `--debug-search`, tambem e criado um relatorio por execucao:

```text
logs/gupy_debug/companies_status_YYYYMMDD_HHMMSS.csv
```

Esse CSV registra `name`, `slug`, `base_url`, `category`, `priority`, `status_http`, `jobs_found`, `jobs_created` e `error` para ajudar a curar slugs e priorizar empresas.

### Pre-filtro tecnico Gupy

Antes de abrir paginas de detalhe, a fonte Gupy aplica um pre-filtro rapido para reduzir ruido e custo de execucao. Ele usa titulo, empresa, localidade, URL, categoria da empresa, prioridade da empresa e texto basico da vaga.

Configuracao em `config/profile_keywords.yaml`:

```yaml
technical_title_keywords:
  - engenharia
  - automacao
  - Python
strong_negative_title_keywords:
  - estagio
  - vendedor
  - loja
weak_negative_title_keywords:
  - assistente
  - auxiliar
location_boost_keywords:
  - Sorocaba
  - Campinas
priority_company_boost: 10
```

O pre-filtro gera:

- `prefilter_score`: ranking rapido para decidir o que manter e enriquecer primeiro.
- `prefilter_reason`: motivo textual da decisao.
- `should_keep`: vagas sem sinais tecnicos suficientes ou com negativo forte podem ser descartadas.
- `should_enrich`: vagas melhores sao priorizadas para abrir pagina de detalhe.

Com `--debug-search`, tambem e criado:

```text
logs/gupy_debug/prefilter_YYYYMMDD_HHMMSS.csv
```

Auditar o pre-filtro apos uma coleta:

```bat
python -m src.main --source gupy --debug-search --dry-run --min-score 0 --analysis-min-score 0 --audit-prefilter
```

Auditar um CSV ja existente:

```bat
python -m src.main --audit-prefilter-only --audit-input logs/gupy_debug/prefilter_YYYYMMDD_HHMMSS.csv
```

A auditoria gera:

```text
reports/prefilter_audit_YYYYMMDD_HHMMSS.md
reports/prefilter_audit_YYYYMMDD_HHMMSS.csv
```

Use o Markdown para revisar:

- vagas mantidas com score baixo, possiveis falsos positivos;
- vagas descartadas com score alto, possiveis falsos negativos;
- vagas descartadas por negativo forte;
- vagas descartadas por falta de termo tecnico;
- empresas, localidades e motivos mais frequentes.

Depois ajuste `config/profile_keywords.yaml`: adicione bons termos em `technical_title_keywords` ou `technical_area_keywords`, e termos ruins em `strong_negative_title_keywords` ou `weak_negative_title_keywords`.

Diferença entre scores:

- `prefilter_score`: usado antes do enriquecimento, para reduzir ruido e ordenar candidatas.
- `match_score`: score principal de aderencia calculado com palavras-chave do perfil, usado no e-mail.
- `fit_score`: analise vaga x perfil/curriculo, calculada depois que a vaga ja esta salva.

### Enriquecimento de detalhes Gupy

Por padrao, a fonte Gupy abre algumas paginas publicas de detalhe da vaga para melhorar a qualidade de `description_snippet`, localidade, requisitos, responsabilidades, beneficios e data de publicacao quando esses dados aparecem no HTML/JSON publico.

Variaveis de ambiente:

```env
GUPY_ENRICH_DETAILS=true
GUPY_MAX_DETAIL_PAGES=10
GUPY_DETAIL_REQUEST_DELAY_SECONDS=1.5
```

- `GUPY_ENRICH_DETAILS`: ativa ou desativa abertura das paginas de detalhe.
- `GUPY_MAX_DETAIL_PAGES`: limita quantas paginas de detalhe sao abertas por execucao.
- `GUPY_DETAIL_REQUEST_DELAY_SECONDS`: intervalo entre requisicoes de detalhe.

Abrir detalhes aumenta o tempo de execucao, mas melhora score, analise vaga x perfil e qualidade do e-mail. Se uma pagina de detalhe falhar, a vaga basica coletada pelo board e preservada.

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

### Revisao humana

O dashboard tem a secao `Revisao Humana` para registrar feedback manual sobre as vagas. Use essa etapa para separar o que realmente vale perseguir do que apenas passou pelas regras automaticas.

Status disponiveis:

- `unreviewed`: ainda nao revisada.
- `relevant`: vaga relevante.
- `irrelevant`: vaga irrelevante.
- `maybe`: revisar depois.
- `applied`: candidatura feita manualmente fora do JobRadar.
- `ignored`: ignorada conscientemente.

Na secao de revisao, selecione uma vaga, confira titulo, empresa, local, `match_score`, `fit_score`, `prefilter_score` e link. Depois salve status, favorita e observacoes. O dashboard tambem permite filtrar por status de revisao e somente favoritas.

Resumo via CLI:

```bat
python -m src.main --review-summary
```

Exportar feedback:

```bat
python -m src.main --export-review-feedback
```

O CSV gerado fica em:

```text
reports/job_review_feedback_YYYYMMDD_HHMMSS.csv
```

Use esse feedback para calibrar `config/profile_keywords.yaml`: vagas relevantes indicam bons termos positivos, vagas irrelevantes e notas recorrentes ajudam a criar termos negativos ou ajustar pesos.

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

- A fonte Gupy publica consulta apenas paginas publicas configuradas em `config/gupy_companies.yaml`.
- A fonte Gupy nao faz login, nao automatiza candidatura e nao tenta contornar captcha ou bloqueios.
- O pre-filtro tecnico reduz ruido, mas ainda pode manter vagas amplas de tecnologia ou descartar casos ambiguos.
- O enriquecimento Gupy abre paginas publicas de detalhe e respeita limite, timeout e delay configuraveis.
- A busca publica depende de resultados de mecanismo de pesquisa.
- Snippets podem ser incompletos e afetar score/analise.
- Buscadores podem variar o HTML, limitar resultados, bloquear requisicoes ou retornar captcha.
- Se a busca publica retornar 0 vagas, rode `--debug-search` para inspecionar status HTTP, tamanho do HTML, links encontrados e filtros aplicados.
- Para maior robustez futura, considere SerpAPI, Bing Search API ou Google Custom Search API.
- A analise vaga x perfil e baseada em regras locais, sem IA externa.
- O dashboard nao coleta dados sozinho; ele apenas le SQLite.
- Envio real depende do SMTP configurado no `.env`.

## Roadmap

- Melhorar fontes com APIs publicas oficiais.
- Melhorar coleta por empresa-alvo.
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
