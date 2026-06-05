# LinkedIn Post

Conclui a versao v3.0.0 do JobRadar Engineer, um projeto de portfolio que transforma uma dor real em um produto local completo: encontrar, filtrar, analisar, revisar e operar um fluxo de vagas publicas aderentes a um perfil tecnico de engenharia, automacao e dados.

A ideia nasceu de um problema pratico. Buscar vagas boas manualmente consome tempo, gera muito ruido e dificulta comparar requisitos, localidades, empresas e aderencia ao perfil.

O JobRadar Engineer resolve esse fluxo com Python:

- coleta vagas publicas de forma controlada;
- usa fonte mock para testes e screenshots seguros com dados ficticios;
- usa GupyPublicSource como fonte real principal;
- mantem busca publica como fallback experimental;
- aplica pre-filtro tecnico para reduzir ruido;
- enriquece vagas por pagina publica de detalhe;
- calcula score de aderencia explicavel;
- gera analise vaga x perfil baseada em regras locais;
- salva tudo em SQLite com schema versionado e indices de performance;
- exibe dashboard Streamlit com revisao humana, historico, alertas, backups e saude do banco;
- gera relatorios locais, backups e checks de publicacao;
- roda CI com Ruff, pytest, coverage e GitHub Actions.

Tecnologias usadas:

Python, SQLite, SQLAlchemy, Streamlit, pytest, Ruff, GitHub Actions, YAML, Requests, BeautifulSoup e Pandas.

Um ponto central foi compliance e seguranca: o projeto nao faz login, nao automatiza candidatura, nao tenta contornar captcha ou bloqueios e trabalha apenas com dados publicos. A demo publica usa dados ficticios, e arquivos como `.env`, banco real, logs, relatorios, runs e backups ficam fora do versionamento.

Status final da release: 198 testes, cobertura local em torno de 91%, limite minimo de 85% no CI, schema versionado e diagnostico de saude do banco.

Feedbacks sao bem-vindos, especialmente sobre arquitetura, operacao local, curadoria de fontes publicas e formas de melhorar a relevancia do ranking mantendo seguranca e transparencia.
