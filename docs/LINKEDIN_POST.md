# LinkedIn Post

Depois de algumas iteracoes, preparei um projeto de portfolio chamado JobRadar Engineer.

A ideia nasceu de uma dor bem pratica: buscar vagas compativeis com um perfil tecnico de engenharia, automacao industrial e dados costuma exigir muita triagem manual. As vagas ficam espalhadas em varias fontes, os requisitos variam bastante e nem sempre e facil perceber rapidamente quais oportunidades realmente combinam com o perfil.

Para resolver isso, desenvolvi um robo local em Python que:

- busca vagas publicas de forma controlada;
- calcula um score de aderencia com base em um perfil configuravel em YAML;
- remove duplicatas;
- salva os resultados em SQLite;
- gera uma analise vaga x perfil baseada em regras locais;
- envia um resumo por e-mail;
- exibe tudo em um dashboard Streamlit;
- permite usar dados ficticios para demonstracao publica.

Tecnologias usadas:

Python, SQLAlchemy, SQLite, Requests, BeautifulSoup, PyYAML, Pandas, Streamlit, APScheduler, pytest e scripts para Windows Task Scheduler.

Um ponto importante do projeto foi o cuidado com compliance: ele nao automatiza login, nao se candidata automaticamente, nao tenta contornar captcha ou bloqueios e trabalha apenas com dados publicos. Tambem preparei o repositorio para GitHub sem versionar `.env`, bancos reais ou logs reais.

O aprendizado tecnico mais interessante foi estruturar o projeto em fases: MVP, score explicavel, dashboard, analise vaga x perfil, agendamento no Windows e preparacao segura para portfolio. Isso ajudou a manter o sistema funcional enquanto novas camadas eram adicionadas.

Feedbacks sao muito bem-vindos, especialmente sobre melhorias de arquitetura, fontes publicas de vagas e formas de deixar a analise de aderencia mais precisa sem depender de dados sensiveis.
