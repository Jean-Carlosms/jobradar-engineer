# JobRadar Engineer - Portfolio Summary

## Nome do projeto

JobRadar Engineer.

## Problema resolvido

Buscar vagas aderentes a um perfil tecnico de engenharia consome tempo, exige comparar requisitos manualmente e pode gerar perda de oportunidades relevantes.

## Solucao criada

Um robo local em Python que coleta vagas publicas, calcula aderencia ao perfil, remove duplicatas, salva em SQLite, envia relatorios por e-mail, analisa vaga x perfil e apresenta tudo em um dashboard Streamlit.

## Principais funcionalidades

- Busca publica segura e fonte mock para validacao.
- Perfil configuravel por YAML.
- Score explicavel por palavras-chave.
- Analise vaga x perfil baseada em regras locais.
- E-mail com melhores vagas e sugestao de mensagem ao recrutador.
- Dashboard com filtros, graficos, exportacao CSV e analises.
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
- `.env`, banco real e logs reais fora do versionamento.

## Resultados alcancados

- MVP executavel com testes automatizados.
- Dashboard local para tomada de decisao.
- Fluxo de e-mail e agendamento Windows.
- Projeto preparado para GitHub sem dados sensiveis.

## Proximos passos

- Melhorar fontes oficiais via APIs publicas.
- Adicionar exportacao Excel.
- Criar favoritos e lista de bloqueio.
- Adicionar pagina detalhada por vaga.
- Configurar CI real no GitHub Actions.

## Como explicar em entrevista

Este projeto mostra como transformei uma dor pessoal de busca de vagas em um produto local completo. Ele combina automacao, dados, engenharia de software, boas praticas de seguranca e uma interface analitica. A arquitetura separa coleta, scoring, persistencia, analise e visualizacao, permitindo evoluir cada parte sem quebrar o MVP.
