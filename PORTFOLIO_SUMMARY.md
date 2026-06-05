# JobRadar Engineer - Portfolio Summary

## Nome do projeto

JobRadar Engineer v3.0.0.

## Problema resolvido

Buscar vagas aderentes a um perfil tecnico de engenharia consome tempo, exige comparar requisitos manualmente e pode gerar perda de oportunidades relevantes.

## Solucao criada

Um robo local em Python que coleta vagas publicas, calcula aderencia ao perfil, remove duplicatas, salva em SQLite, analisa vaga x perfil, envia relatorios por e-mail, permite revisao humana e apresenta tudo em um dashboard Streamlit.

## Status v3.0.0

Metricas finais da release: `198 testes`, cobertura local em torno de `91%`, limite minimo de cobertura `85%` no CI, schema SQLite versionado e banco local validado com `16 indices`.

Projeto completo para portfolio e publicacao segura, agora com CI real, cobertura de testes, qualidade automatizada, testes offline determinísticos, observabilidade local, alertas operacionais por e-mail, dashboard de alertas operacionais, dashboard de backups, retencao segura de backups, backup e manutencao do SQLite, historico operacional, calibracao assistida por feedback humano, dashboard polido e estrutura visual preparada para screenshots publicos. O fluxo local cobre configuracao do perfil, coleta, ranking, auditoria, revisao humana, insights, relatorios de execucao, backup, visualizacao, operacao no Windows e validacao continua no GitHub Actions.

## Pipeline final

1. Carrega perfil profissional em YAML.
2. Coleta vagas por fonte mock, busca publica ou Gupy publica.
3. Deduplica por URL e identidade da vaga.
4. Aplica pre-filtro tecnico para reduzir ruido.
5. Enriquece as melhores vagas Gupy por pagina publica de detalhe.
6. Calcula `match_score` e justificativa explicavel.
7. Persiste em SQLite com migracoes locais simples.
8. Gera analise vaga x perfil com `fit_score`.
9. Envia e-mail em dry-run ou SMTP configurado.
10. Exibe dashboard Streamlit com filtros, graficos, auditoria e revisao humana.
11. Registra relatorios de execucao e historico operacional.
12. Gera alertas operacionais para falhas, zero vagas e execucoes sem elegiveis.
13. Mantem backups, retencao segura e manutencao do SQLite local.
14. Controla schema versionado, indices de performance e saude do banco.
15. Exporta auditorias, feedbacks, resumo do banco e health reports para `reports/`.

## Principais funcionalidades

- Busca publica segura, fonte mock e fonte Gupy publica dedicada.
- Perfil configuravel por YAML.
- Curadoria de empresas-alvo Gupy por categoria.
- Pre-filtro tecnico e ranking de relevancia.
- Enriquecimento de vagas por pagina publica de detalhe.
- Score explicavel por palavras-chave.
- Analise vaga x perfil baseada em regras locais.
- E-mail com melhores vagas e sugestao de mensagem ao recrutador.
- Alertas operacionais separados para falhas e resumos de execucao.
- Backup, restore protegido, resumo agregado e manutencao do SQLite local.
- Retencao de backups com dry-run, confirmacao explicita e relatorios de limpeza.
- Schema SQLite versionado com migracoes locais idempotentes.
- Indices de performance e diagnostico de saude do banco por CLI, dashboard e relatorios.
- Cobertura de testes medida localmente com pytest-cov e integrada ao CI.
- Politica de cobertura minima de 85% aplicada no CI.
- Cobertura reforcada em modulos criticos como CLI operacional, backup, alertas e envio de e-mail.
- Revisao arquitetural de modulos experimentais e fontes fallback documentada.
- Gerenciamento seguro de conexoes SQLite para reduzir `ResourceWarning` na suite.
- Dashboard com filtros, graficos, exportacao CSV, auditoria, revisao humana, historico, alertas operacionais e backups.
- Feedback manual com status, favoritos e notas.
- Insights assistivos para calibrar o perfil sem alterar YAML automaticamente.
- Scripts Windows para dry-run, producao e dashboard.
- Banco ficticio para portfolio.

## Tecnologias usadas

Python, SQLAlchemy, SQLite, Requests, BeautifulSoup, PyYAML, Pandas, Streamlit, APScheduler e pytest.

## Decisoes tecnicas

- SQLite local para simplicidade e portabilidade.
- YAML para separar perfil profissional do codigo.
- Regras locais para analise sem depender de API externa.
- Scripts `.bat` para compatibilidade direta com Windows Task Scheduler.
- Dados ficticios separados em `examples/` para demonstracao publica.

## Cuidados de compliance

- Sem login automatizado.
- Sem candidatura automatica.
- Sem bypass de captcha ou bloqueios.
- Uso apenas de dados publicos de vagas.
- `.env`, `.venv/`, banco real, logs reais e relatorios gerados fora do versionamento.

## Resultados alcancados

- Versao v3.0.0 executavel com 198 testes automatizados offline, cobertura local em torno de 91%, schema SQLite versionado, 16 indices de performance, saude do banco, limite minimo de 85% no CI, revisao arquitetural de modulos experimentais, warnings SQLite limpos, insights de feedback, relatorios de execucao, alertas operacionais, backups do SQLite, retencao segura, historico operacional no dashboard, dashboard de alertas, dashboard de backups e README visual.
- Dashboard local para tomada de decisao.
- Fluxo de e-mail e agendamento Windows.
- Projeto preparado para GitHub sem dados sensiveis.
- Auditoria e revisao humana para calibrar relevancia.

## Como demonstrar visualmente

Use somente `Dados ficticios` no dashboard para qualquer demo publica. O fluxo recomendado e abrir `streamlit run dashboard.py`, selecionar `Dados ficticios`, mostrar `Resumo Executivo`, explicar o funil Coleta -> Pre-filtro -> Match -> Analise -> Revisao e depois abrir uma vaga para mostrar analise, revisao humana e insights.

Prints recomendados:

- `docs/images/dashboard-overview.png`
- `docs/images/job-funnel.png`
- `docs/images/top-jobs.png`
- `docs/images/job-profile-analysis.png`
- `docs/images/human-review.png`
- `docs/images/prefilter-audit.png`
- `docs/images/feedback-insights.png`

## Evidencias visuais

Os prints publicos devem usar apenas o banco ficticio `data/sample_jobs.db`, selecionando `Dados ficticios` no dashboard.

Screenshots esperados:

- `docs/images/dashboard-overview.png`
- `docs/images/job-funnel.png`
- `docs/images/top-jobs.png`
- `docs/images/job-profile-analysis.png`
- `docs/images/human-review.png`
- `docs/images/prefilter-audit.png`
- `docs/images/feedback-insights.png`

Enquanto os PNGs finais nao forem capturados, os arquivos `.placeholder.txt` em `docs/images/` documentam exatamente qual tela capturar e como revisar privacidade.

## Proximos passos

- Avaliar Alembic caso o schema cresca alem das migracoes locais simples.
- Integrar APIs oficiais de busca de forma opcional.
- Subir cobertura minima para 90% depois de cobrir os modulos restantes.
- Avaliar criptografia opcional de backups.
- Criar deploy/demo opcional e melhorias visuais finais.

## Como explicar em entrevista

Este projeto mostra como transformei uma dor pessoal de busca de vagas em um produto local completo. Ele combina automacao, dados, engenharia de software, boas praticas de seguranca, auditoria de regras e uma interface analitica. A arquitetura separa coleta, scoring, persistencia, analise, revisao humana e visualizacao, permitindo evoluir cada parte sem quebrar o fluxo principal.
