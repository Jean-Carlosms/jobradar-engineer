# JobRadar Engineer

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
[![CI](https://github.com/Jean-Carlosms/jobradar-engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/Jean-Carlosms/jobradar-engineer/actions/workflows/ci.yml)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-red)
![SQLite](https://img.shields.io/badge/SQLite-local-lightgrey)
![Status](https://img.shields.io/badge/Status-v3.0.0-success)
![Coverage](https://img.shields.io/badge/Coverage-measured%20locally-informational)

## Visao geral

JobRadar Engineer e um robo local em Python para buscar, pontuar, analisar e visualizar vagas publicas aderentes a um perfil de engenharia mecatronica, automacao industrial, dados industriais, Python, Power BI, CLP/PLC, robotica e Industria 4.0.

O projeto foi preparado para uso local e apresentacao em portfolio, com dados ficticios, dashboard Streamlit, testes automatizados e cuidados para nao versionar informacoes sensiveis.

Status atual: `v3.0.0 - Indices de performance e saude do banco`.

Qualidade atual: `198 testes`, cobertura local em torno de `91%`, limite minimo de cobertura `85%` no CI, schema SQLite versionado e diagnostico de saude do banco por CLI/dashboard.

## Problema

Buscar vagas compativeis com um perfil tecnico exige consultar varias fontes, filtrar resultados pouco aderentes, comparar requisitos e lembrar quais vagas ja foram enviadas ou analisadas.

## Solucao

O sistema coleta vagas publicas, calcula score explicavel, remove duplicatas, salva em SQLite, gera analise vaga x perfil, envia relatorios por e-mail e exibe tudo em um dashboard local.

## Pipeline final

1. Carrega perfil e empresas-alvo a partir de YAML.
2. Coleta vagas por fonte mock, busca publica ou Gupy publica.
3. Deduplica vagas por URL e identidade.
4. Aplica pre-filtro tecnico para reduzir ruido.
5. Enriquece melhores vagas Gupy por pagina publica de detalhe.
6. Calcula `match_score` explicavel.
7. Persiste dados e migracoes simples em SQLite.
8. Gera analise vaga x perfil com `fit_score`.
9. Envia relatorio de vagas em dry-run ou SMTP.
10. Exibe dashboard com filtros, graficos, auditoria, revisao humana e historico operacional.
11. Gera relatorios de execucao e alertas operacionais opcionais.
12. Cria backups e manutencao segura do SQLite local.
13. Exporta auditorias, feedbacks e resumos em CSV/Markdown/JSON.

## Funcionalidades

- Fonte mock e busca publica por mecanismo de pesquisa.
- Fonte Gupy publica dedicada com curadoria por empresa, fonte real principal do projeto.
- Pre-filtro tecnico e auditoria de relevancia.
- Enriquecimento por pagina publica de detalhe.
- Perfil profissional configuravel por YAML.
- Score de aderencia com justificativa.
- Deduplicacao por URL e por titulo + empresa + local.
- Persistencia em SQLite.
- Analise vaga x perfil/curriculo baseada em regras locais.
- E-mail com melhores vagas e resumo de analise.
- Alertas operacionais por e-mail para falhas, zero vagas e execucoes sem elegiveis.
- Backup, restauracao protegida e manutencao do SQLite local.
- Dashboard Streamlit com filtros, graficos, historico operacional, alertas operacionais e exportacao CSV.
- Revisao humana com status, favoritas e notas.
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

No PowerShell, se necessario, use:

```powershell
.\.venv\Scripts\Activate.ps1
```

Configure o ambiente:

```bat
copy .env.example .env
```

## Principais comandos

Coleta simulada com analise e sem envio real:

```bat
python -m src.main --source mock --analyze --dry-run --min-score 50 --analysis-min-score 50
```

Gupy real em dry-run:

```bat
python -m src.main --source gupy --debug-search --analyze --dry-run --min-score 0 --analysis-min-score 0
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

Resumo de revisao humana:

```bat
python -m src.main --review-summary
```

Exportar feedback humano:

```bat
python -m src.main --export-review-feedback
```

Gerar insights assistivos a partir do feedback humano:

```bat
python -m src.main --feedback-insights
python -m src.main --feedback-insights --feedback-insights-min-reviewed 5
```

Gerar relatório local da execução:

```bat
python -m src.main --source mock --dry-run --run-report
python -m src.main --latest-run-report
python -m src.main --run-history-summary
python -m src.main --operational-alerts-summary
python -m src.main --test-operational-alert --dry-run
```

Backup e manutencao do banco local:

```bat
python -m src.main --backup-db --backup-reason "manual"
python -m src.main --list-db-backups
python -m src.main --db-backup-summary
python -m src.main --verify-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json
python -m src.main --restore-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json --confirm-restore
python -m src.main --export-db-summary
python -m src.main --db-maintenance
python -m src.main --cleanup-db-backups-dry-run
python -m src.main --cleanup-db-backups --confirm-cleanup-backups
python -m src.main --schema-status
python -m src.main --migrate-schema
```

Auditar pre-filtro:

```bat
python -m src.main --audit-prefilter-only --audit-input logs/gupy_debug/prefilter_YYYYMMDD_HHMMSS.csv
```

Rodar testes:

```bat
python -m pytest
```

Os testes são offline e determinísticos: durante `pytest`, chamadas reais de rede via `requests` são bloqueadas por padrão. Testes que precisarem de rede devem ser marcados explicitamente com `@pytest.mark.network`, mas a coleta real deve ser validada manualmente pelos comandos da CLI.

Rodar validacoes de qualidade locais:

```bat
python scripts\check_publication_safety.py
python -m ruff check .
python -m pytest
```

## Cobertura de testes

A cobertura e medida localmente com `pytest-cov`. O limite minimo atual no CI e `85%`, com cobertura local em torno de `91%`:

```bat
python -m pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=85
```

O relatorio HTML fica em:

```text
htmlcov/
```

`htmlcov/`, `.coverage` e `coverage.xml` nao sao versionados.

A suite tambem pode ser rodada com warnings explicitos para validar conexoes SQLite e outros recursos:

```bat
python -W default -m pytest
```

O objetivo e manter os testes offline, deterministicos e sem `ResourceWarning` relevante.

Para instalar dependencias de desenvolvimento:

```bat
python -m pip install -r requirements-dev.txt
```

Diferença entre testes e execução real:

- `python -m pytest`: valida parsers, scoring, banco, dashboard e CLI usando fixtures, mocks e dados locais.
- `python -m src.main --source gupy --dry-run`: executa coleta real em páginas públicas configuradas.
- `python -m src.main --source search --dry-run`: executa busca pública real, sujeita a bloqueios, HTML variável e disponibilidade da internet.

## Como rodar com dados ficticios

Os dados de exemplo sao ficticios e seguros para portfolio.

```bat
python scripts\load_sample_data.py
```

Isso cria:

```text
data/sample_jobs.db
```

Esse banco nao sobrescreve `data/jobs.db`.

Abra o dashboard e selecione `Dados ficticios` na barra lateral:

```bat
streamlit run dashboard.py
```

Use esse modo para screenshots e portfolio publico.

## Como rodar com Gupy real

```bat
python -m src.main --source gupy --debug-search --analyze --dry-run --min-score 0 --analysis-min-score 0
```

Esse comando consulta apenas paginas publicas configuradas em `config/gupy_companies.yaml`, nao faz login, nao automatiza candidatura e nao tenta contornar captcha ou bloqueios.

## Fonte Gupy publica

A fonte dedicada da Gupy e a fonte real principal do projeto. Ela reduz a dependencia de buscadores HTML e consulta paginas publicas configuradas. Configure empresas em:

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
- `--source gupy`: usa apenas paginas publicas Gupy configuradas; e a fonte principal para coleta real.
- `--source search`: usa busca publica via mecanismo de pesquisa; e fallback experimental, sujeito a HTML variavel, bloqueios e challenge/captcha.
- `--source all`: usa Gupy publica + BuscaPublica.
- `--include-mock-in-all`: inclui mock tambem em `all`, somente quando solicitado.

Com `--debug-search`, a fonte Gupy salva HTML sanitizado e links extraidos em `logs/gupy_debug/`.

A revisao arquitetural dos modulos experimentais e de baixa cobertura esta documentada em:

```text
docs/COVERAGE_REVIEW.md
```

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

O dashboard esta organizado em abas para demonstracao:

- `Resumo Executivo`: visao inicial com metricas principais e pipeline.
- `Funil de Vagas`: Coleta -> Pre-filtro -> Match -> Analise -> Revisao.
- `Top Vagas`: ranking das melhores oportunidades filtradas.
- `Analise Vaga x Perfil`: fit score, competencias, lacunas e mensagem sugerida.
- `Revisao Humana`: status, favorita e notas manuais.
- `Auditoria do Pre-filtro`: leitura do CSV de debug mais recente.
- `Insights de Feedback`: resumo das revisoes humanas.
- `Historico de Execucoes`: metricas de execucoes anteriores geradas em `runs/`.
- `Alertas Operacionais`: falhas, execucoes sem vagas e alertas enviados a partir de `runs/*.json`.
- `Backups e Banco`: manifestos de backup, metricas, CSV e comandos de manutencao.
- `Exportacoes`: CSVs e comandos auxiliares.

## Como revisar vagas no dashboard

1. Rode uma coleta real ou carregue dados ficticios.
2. Abra `streamlit run dashboard.py`.
3. Use os filtros laterais para escolher fonte, empresa, score, status e favoritas.
4. Na secao `Revisao Humana`, selecione a vaga.
5. Marque status: `relevant`, `irrelevant`, `maybe`, `applied` ou `ignored`.
6. Marque favorita quando fizer sentido.
7. Escreva observacoes para calibrar o YAML depois.
8. Use `python -m src.main --export-review-feedback` para gerar CSV em `reports/`.

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

### Insights de feedback

Depois de revisar vagas no dashboard, gere um relatorio assistivo:

```bat
python -m src.main --feedback-insights
```

Com minimo de revisoes esperado:

```bat
python -m src.main --feedback-insights --feedback-insights-min-reviewed 5
```

Isso cria:

```text
reports/feedback_insights_YYYYMMDD_HHMMSS.md
reports/feedback_insights_YYYYMMDD_HHMMSS.csv
```

O relatorio sugere termos candidatos a positivos e negativos, empresas para priorizar, empresas com ruido, titulos recorrentes, localidades relevantes, possiveis falsos positivos, possiveis falsos negativos e vagas favoritas. As sugestoes sao assistivas: o sistema nao altera `config/profile_keywords.yaml` automaticamente.

Use o Markdown para decidir ajustes manuais em `high_weight_keywords`, `medium_weight_keywords`, `negative_keywords`, listas tecnicas/negativas do pre-filtro, `priority_companies` e `location_boost_keywords`. Se houver poucas vagas revisadas, o relatorio ainda e gerado, mas marca baixa confianca.

### Relatórios de execução

Execuções reais ou dry-run podem gerar relatórios locais em `runs/`:

```text
runs/run_report_YYYYMMDD_HHMMSS.md
runs/run_report_YYYYMMDD_HHMMSS.json
```

Ative explicitamente com:

```bat
python -m src.main --source mock --dry-run --run-report
```

Veja o relatório mais recente:

```bat
python -m src.main --latest-run-report
```

Veja um resumo curto do historico:

```bat
python -m src.main --run-history-summary
python -m src.main --operational-alerts-summary
```

No dashboard, a aba `Historico de Execucoes` le os JSONs de `runs/`, mostra totais, duracao media, e-mails enviados, execucoes com erro, alertas, fonte mais usada, tabela filtravel e exportacao CSV do historico.

A aba `Alertas Operacionais` tambem usa `runs/*.json`, mas foca apenas nos campos `operational_alert_*`: tipo do alerta, se foi enviado, motivo/status, fonte, modo, vagas unicas, vagas elegiveis e caminho do Markdown. Ela permite filtrar por tipo, envio, fonte e modo, alem de exportar CSV dos alertas filtrados.

Os relatórios registram `run_id`, horários, duração, modo, fonte selecionada, fontes executadas, vagas coletadas por fonte, vagas únicas, status de e-mail, erros por fonte e caminhos de relatórios/debug gerados. Eles são sanitizados para evitar credenciais e `.env`, e `runs/` não é versionado.

Diferenca entre `logs/` e `runs/`:

- `logs/`: arquivos de diagnostico operacional, HTML sanitizado, CSVs de debug e saidas de scripts.
- `runs/`: relatorios estruturados Markdown/JSON por execucao, usados para historico operacional e auditoria local.

### Alertas operacionais

O JobRadar pode gerar e-mails operacionais separados do e-mail de vagas. O e-mail de vagas lista oportunidades recomendadas; o e-mail operacional resume a saude da execucao, fontes com erro e situacoes que merecem atencao.

Tipos de alerta:

- `failure`: uma ou mais fontes registraram erro.
- `no_jobs`: nenhuma vaga unica foi coletada.
- `no_email_eligible`: houve coleta, mas nenhuma vaga ficou elegivel para e-mail.
- `success_summary`: resumo opcional de execucao bem-sucedida.

Variaveis do `.env`:

```text
OPERATIONAL_ALERTS_ENABLED=false
OPERATIONAL_ALERTS_ON_FAILURE=true
OPERATIONAL_ALERTS_ON_NO_JOBS=true
OPERATIONAL_ALERTS_ON_NO_EMAIL_ELIGIBLE=false
OPERATIONAL_DAILY_SUMMARY=false
```

Teste o template sem envio real:

```bat
python -m src.main --test-operational-alert --dry-run
```

Forcar alertas em uma execucao dry-run:

```bat
python -m src.main --source mock --dry-run --run-report --send-operational-alerts
```

Desativar alertas em uma execucao especifica:

```bat
python -m src.main --source all --dry-run --run-report --no-operational-alerts
```

Uso recomendado no Agendador do Windows: mantenha `--run-report` ativo nos scripts, valide com `--dry-run` e ative `OPERATIONAL_ALERTS_ENABLED=true` apenas quando o SMTP estiver testado. Em dry-run, o alerta e montado e registrado em log, mas nao e enviado de verdade.

### Backup e manutencao do banco local

O banco local `data/jobs.db` guarda vagas coletadas, revisoes humanas, favoritas, analises e status de envio. A Fase 24 adiciona backup e restauracao segura para proteger esse historico.

Criar backup manual:

```bat
python -m src.main --backup-db --backup-reason "antes de ajustes"
```

Isso gera:

```text
backups/jobs_backup_YYYYMMDD_HHMMSS.db
backups/jobs_backup_YYYYMMDD_HHMMSS.json
```

O manifesto JSON registra timestamp, banco de origem, arquivo de backup, tamanho, SHA-256 e motivo. Ele nao inclui credenciais nem conteudo das vagas.

Listar e verificar backups:

```bat
python -m src.main --list-db-backups
python -m src.main --db-backup-summary
python -m src.main --verify-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json
```

No dashboard, a aba `Backups e Banco` le os manifestos `backups/jobs_backup_*.json`, mostra total de backups, tamanho total, backup mais recente, maior backup, tabela exportavel em CSV e comandos recomendados. A restauracao nao esta disponivel no dashboard nesta fase.

Restaurar exige confirmacao explicita:

```bat
python -m src.main --restore-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json --confirm-restore
```

Antes de restaurar, o sistema cria automaticamente um backup do estado atual. Sem `--confirm-restore`, a restauracao falha de proposito.

Exportar resumo e executar manutencao SQLite:

```bat
python -m src.main --export-db-summary
python -m src.main --db-maintenance
```

`--export-db-summary` gera CSV/JSON em `reports/` com contagens e metricas agregadas do banco. `--db-maintenance` executa `VACUUM` e `ANALYZE` com checagem de integridade antes/depois.

Backups reais nao sao versionados: `.gitignore` protege `backups/*` e permite apenas `backups/.gitkeep`.

Retencao e limpeza segura:

```bat
python -m src.main --cleanup-db-backups-dry-run
python -m src.main --cleanup-db-backups
python -m src.main --cleanup-db-backups --confirm-cleanup-backups
```

`--cleanup-db-backups-dry-run` gera plano e relatorios sem apagar nada. `--cleanup-db-backups` sem confirmacao tambem se comporta como dry-run por seguranca. A remocao real so ocorre com `--confirm-cleanup-backups`, nunca remove o backup mais recente e protege manifestos invalidos por padrao.

Relatorios de limpeza:

```text
reports/backup_cleanup_YYYYMMDD_HHMMSS.md
reports/backup_cleanup_YYYYMMDD_HHMMSS.csv
```

## Schema versionado, indices e saude do banco

O SQLite local usa uma tabela simples de controle chamada `schema_migrations` para registrar a versao aplicada do schema. A versao atual esperada e validada pelo projeto fica em `src/schema_migrations.py`.

Verificar status:

```bat
python -m src.main --schema-status
```

Aplicar migracoes pendentes:

```bat
python -m src.main --migrate-schema
```

Antes de migrar um banco real, crie backup:

```bat
python -m src.main --backup-db --backup-reason "before schema migration"
python -m src.main --migrate-schema
```

As migracoes sao idempotentes, locais e nao destroem dados existentes. O projeto ainda nao usa Alembic para manter a operacao local simples; se o schema crescer muito, essa avaliacao entra no roadmap.

A versao 2 do schema adiciona indices idempotentes para consultas comuns do dashboard e da CLI, incluindo campos como URL, titulo, empresa, fonte, scores, revisao, favoritos, envio e relacao com analises.

Verificar saude do banco:

```bat
python -m src.main --db-health
```

Exportar relatorio de saude:

```bat
python -m src.main --export-db-health
```

Os relatorios sao gerados em:

```text
reports/db_health_YYYYMMDD_HHMMSS.json
reports/db_health_YYYYMMDD_HHMMSS.md
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

Os scripts Windows de dry-run e produção usam `--run-report`, então cada execução agendada também deixa um resumo local em `runs/`.

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
- `.env`, `.venv/`, `data/jobs.db`, `logs/`, `reports/`, `runs/` e `backups/` nao devem ser versionados.
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

## Demonstração visual

Os screenshots publicos devem usar apenas `Dados ficticios` no dashboard. Imagens recomendadas:

- `docs/images/dashboard-overview.png`: resumo executivo.
- `docs/images/job-funnel.png`: funil de vagas.
- `docs/images/top-jobs.png`: top vagas.
- `docs/images/job-profile-analysis.png`: analise vaga x perfil.
- `docs/images/human-review.png`: revisao humana.
- `docs/images/prefilter-audit.png`: auditoria do pre-filtro.
- `docs/images/feedback-insights.png`: insights de feedback.

Se as imagens `.png` ainda nao estiverem presentes, siga `docs/SCREENSHOTS_GUIDE.md` e use os placeholders em `docs/images/` como checklist seguro.

Roteiro de demo: `docs/DEMO_SCRIPT.md`.

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
python -m ruff check .
python scripts\check_publication_safety.py
python -W default -m pytest
python -m pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=85
python -m src.main --schema-status
python -m src.main --db-health
```

## Status do projeto

Versao atual: `v3.0.0 - Indices de performance e saude do banco`.

Testes:

```bat
python scripts\check_publication_safety.py
python -m ruff check .
python -m pytest
```
