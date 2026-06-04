# JobRadar Engineer - Portfolio Summary

## Nome do projeto

JobRadar Engineer v1.3.0.

## Problema resolvido

Buscar vagas aderentes a um perfil tecnico de engenharia consome tempo, exige comparar requisitos manualmente e pode gerar perda de oportunidades relevantes.

## Solucao criada

Um robo local em Python que coleta vagas publicas, calcula aderencia ao perfil, remove duplicatas, salva em SQLite, analisa vaga x perfil, envia relatorios por e-mail, permite revisao humana e apresenta tudo em um dashboard Streamlit.

## Status v1.3.0

Projeto completo para portfolio e publicacao segura, agora com CI real, qualidade automatizada, calibracao assistida por feedback humano e dashboard polido para demonstracao visual. O fluxo local cobre configuracao do perfil, coleta, ranking, auditoria, revisao humana, insights, visualizacao, operacao no Windows e validacao continua no GitHub Actions.

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
11. Exporta auditorias e feedbacks para `reports/`.

## Principais funcionalidades

- Busca publica segura, fonte mock e fonte Gupy publica dedicada.
- Perfil configuravel por YAML.
- Curadoria de empresas-alvo Gupy por categoria.
- Pre-filtro tecnico e ranking de relevancia.
- Enriquecimento de vagas por pagina publica de detalhe.
- Score explicavel por palavras-chave.
- Analise vaga x perfil baseada em regras locais.
- E-mail com melhores vagas e sugestao de mensagem ao recrutador.
- Dashboard com filtros, graficos, exportacao CSV, auditoria e revisao humana.
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

- Versao v1.3.0 executavel com testes automatizados, CI no GitHub Actions, insights de feedback e demo visual.
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

## Proximos passos

- Gerar sugestoes semi-automaticas de ajuste do YAML com base no feedback humano.
- Melhorar fontes oficiais via APIs publicas.
- Adicionar exportacao Excel.
- Adicionar pagina detalhada por vaga.
- Configurar CI real no GitHub Actions.

## Como explicar em entrevista

Este projeto mostra como transformei uma dor pessoal de busca de vagas em um produto local completo. Ele combina automacao, dados, engenharia de software, boas praticas de seguranca, auditoria de regras e uma interface analitica. A arquitetura separa coleta, scoring, persistencia, analise, revisao humana e visualizacao, permitindo evoluir cada parte sem quebrar o fluxo principal.
