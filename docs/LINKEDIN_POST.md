# LinkedIn Post

Conclui a versao v1.0.0 do JobRadar Engineer, um projeto de portfolio que transforma uma dor real em um produto local completo: encontrar, filtrar, analisar e revisar vagas publicas aderentes a um perfil tecnico de engenharia, automacao e dados.

A ideia nasceu de um problema pratico. Buscar vagas boas manualmente consome tempo, gera muito ruido e dificulta comparar requisitos, localidades, empresas e aderencia ao perfil.

O JobRadar Engineer resolve esse fluxo com Python:

- coleta vagas publicas de forma controlada;
- usa fonte mock para testes e screenshots seguros;
- consulta paginas publicas da Gupy configuradas por empresa;
- aplica pre-filtro tecnico para reduzir ruido;
- enriquece vagas por pagina publica de detalhe;
- calcula score de aderencia explicavel;
- gera analise vaga x perfil baseada em regras locais;
- salva tudo em SQLite;
- envia resumo por e-mail em dry-run ou SMTP configurado;
- exibe dashboard Streamlit com filtros, graficos e exportacao;
- permite revisao humana com status, favoritas e notas;
- gera auditorias e feedbacks para calibrar o perfil.

Tecnologias usadas:

Python, SQLAlchemy, SQLite, Requests, BeautifulSoup, PyYAML, Pandas, Streamlit, APScheduler, pytest e scripts para Windows Task Scheduler.

Um ponto central foi compliance e seguranca: o projeto nao faz login, nao automatiza candidatura, nao tenta contornar captcha ou bloqueios e trabalha apenas com dados publicos. Tambem foi preparado para GitHub sem versionar `.env`, banco real, logs ou relatorios locais.

O aprendizado mais valioso foi evoluir o produto em fases sem quebrar o MVP: coleta, scoring, dashboard, analise, agendamento, fonte Gupy, pre-filtro, auditoria, revisao humana e consolidacao para release.

Feedbacks sao bem-vindos, especialmente sobre arquitetura, curadoria de fontes publicas e formas de melhorar a relevancia do ranking mantendo seguranca e transparencia.
