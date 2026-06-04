# Interview Pitch

## Pitch de 30 segundos

O JobRadar Engineer v1.0.0 e um robo local em Python para triagem de vagas publicas. Ele coleta oportunidades, deduplica, aplica pre-filtro tecnico, enriquece vagas Gupy por pagina publica, calcula aderencia ao perfil, gera analise vaga x curriculo, envia resumo por e-mail e mostra tudo em um dashboard Streamlit com revisao humana. O projeto inclui testes, SQLite, scripts Windows, auditoria de regras e cuidados para publicacao segura no GitHub.

## Explicacao tecnica de 2 minutos

O projeto foi construido em camadas. A primeira camada coleta vagas por fonte mock, busca publica controlada e uma fonte Gupy publica dedicada. Todas seguem regras de compliance: sem login, sem candidatura automatica e sem bypass de captcha ou bloqueios.

Depois da coleta, o sistema deduplica vagas por URL e identidade, aplica um pre-filtro tecnico configurado por YAML e prioriza quais vagas merecem enriquecimento. A fonte Gupy abre paginas publicas de detalhe com timeout, rate limit e fallback seguro. Em seguida, o matcher calcula `match_score` explicavel, e o analisador local gera `fit_score`, skills encontradas, lacunas, riscos e mensagem sugerida.

Os dados sao persistidos em SQLite via SQLAlchemy, com migracoes simples para evoluir o modelo. O dashboard em Streamlit usa Pandas para metricas, filtros, graficos, tabelas, auditoria do pre-filtro e revisao humana. A revisao permite marcar vaga como relevante, irrelevante, talvez, aplicada ou ignorada, alem de favorita e notas.

Para operacao, existem scripts Windows `.bat`, logs locais, envio de e-mail em dry-run ou SMTP configurado e comandos CLI para auditoria, resumo de feedback e exportacao CSV. Para portfolio, o projeto tem dados ficticios, banco de exemplo, checklist de publicacao, release notes e safety check automatizado.

## Decisoes de arquitetura

- SQLite para portabilidade e simplicidade local.
- SQLAlchemy para modelo e migracoes simples.
- YAML para separar perfil profissional, empresas-alvo e resumo do perfil.
- Streamlit para dashboard local rapido.
- Regras locais para scoring e analise, sem depender de API externa.
- CSV/Markdown para auditorias e feedbacks rastreaveis.
- Scripts Windows para operacao no ambiente alvo.
- Dados ficticios separados para screenshots e publicacao.

## Desafios encontrados

- Reduzir ruido de milhares de vagas publicas sem perder boas oportunidades.
- Criar score explicavel e auditavel.
- Lidar com HTML publico instavel e slugs Gupy invalidos.
- Preservar seguranca: sem credenciais, banco real, logs ou relatorios no Git.
- Evoluir em fases mantendo testes e compatibilidade.

## Relacao com engenharia, automacao e dados

O projeto combina automacao de processos, engenharia de software, modelagem de dados, ETL leve, ranking, auditoria e visualizacao. Ele transforma informacao publica dispersa em uma base local consultavel, explicavel e revisavel.

## Proximos passos

- Ajuste semi-automatico de pesos com base no feedback humano.
- Sugestoes de novos termos positivos e negativos para `profile_keywords.yaml`.
- Integracao opcional com APIs oficiais de busca.
- CI com GitHub Actions.
- Pagina detalhada por vaga no dashboard.
