# Interview Pitch

## Pitch de 30 segundos

O JobRadar Engineer v3.0.0 e um robo local em Python para triagem e operacao de vagas publicas. Ele coleta oportunidades, deduplica, aplica pre-filtro tecnico, enriquece vagas Gupy por pagina publica, calcula aderencia ao perfil, gera analise vaga x curriculo, envia resumo por e-mail e mostra tudo em um dashboard Streamlit com revisao humana, historico, alertas, backups e saude do banco. O projeto inclui CI, 198 testes, coverage, SQLite com schema versionado, scripts Windows, auditoria de regras e cuidados para publicacao segura no GitHub.

## Explicacao tecnica de 2 minutos

O projeto foi construido em camadas. A primeira camada coleta vagas por fonte mock, busca publica controlada e uma fonte Gupy publica dedicada. Todas seguem regras de compliance: sem login, sem candidatura automatica e sem bypass de captcha ou bloqueios.

Depois da coleta, o sistema deduplica vagas por URL e identidade, aplica um pre-filtro tecnico configurado por YAML e prioriza quais vagas merecem enriquecimento. A GupyPublicSource e a fonte real principal e abre paginas publicas de detalhe com timeout, rate limit e fallback seguro. A busca publica fica como fallback experimental. Em seguida, o matcher calcula `match_score` explicavel, e o analisador local gera `fit_score`, skills encontradas, lacunas, riscos e mensagem sugerida.

Os dados sao persistidos em SQLite via SQLAlchemy, com schema versionado, migracoes locais idempotentes, indices de performance e diagnostico de saude do banco. O dashboard em Streamlit usa Pandas para metricas, filtros, graficos, tabelas, auditoria do pre-filtro, revisao humana, historico operacional, alertas, backups e banco. A revisao permite marcar vaga como relevante, irrelevante, talvez, aplicada ou ignorada, alem de favorita e notas.

Para operacao, existem scripts Windows `.bat`, logs locais, run reports, alertas operacionais por e-mail, backup/restauracao protegida, manutencao do banco, health reports e comandos CLI para auditoria, feedback e exportacoes. Para portfolio, o projeto tem dados ficticios, banco de exemplo, checklist de publicacao, release notes, safety check automatizado e demo visual segura.

Qualidade: GitHub Actions roda Ruff, safety check e pytest com coverage. A release v3.0.0 fecha com 198 testes, cobertura local em torno de 91% e limite minimo de 85% no CI.

## Decisoes de arquitetura

- SQLite para portabilidade e simplicidade local.
- SQLAlchemy para modelo e migracoes simples.
- YAML para separar perfil profissional, empresas-alvo e resumo do perfil.
- Streamlit para dashboard local rapido.
- Regras locais para scoring e analise, sem depender de API externa.
- CSV/Markdown/JSON para auditorias, feedbacks, historico e saude do banco.
- Scripts Windows para operacao no ambiente alvo.
- Dados ficticios separados para screenshots e publicacao.
- CI, coverage e testes offline para evitar dependencia de internet real durante pytest.
- Schema SQLite versionado sem Alembic nesta fase para manter a operacao local simples.

## Desafios encontrados

- Reduzir ruido de milhares de vagas publicas sem perder boas oportunidades.
- Criar score explicavel e auditavel.
- Lidar com HTML publico instavel e slugs Gupy invalidos.
- Preservar seguranca: sem credenciais, banco real, logs ou relatorios no Git.
- Evoluir em fases mantendo testes e compatibilidade.

## Relacao com engenharia, automacao e dados

O projeto combina automacao de processos, engenharia de software, modelagem de dados, ETL leve, ranking, auditoria, observabilidade local e visualizacao. Ele transforma informacao publica dispersa em uma base local consultavel, explicavel e revisavel.

## Proximos passos

- Integracao opcional com APIs oficiais de busca.
- Avaliar Alembic se o schema crescer.
- Subir limite de cobertura para 90%.
- Pagina detalhada por vaga no dashboard.
