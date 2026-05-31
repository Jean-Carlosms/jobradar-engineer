# Interview Pitch

## Pitch de 30 segundos

O JobRadar Engineer e um robo local em Python que automatiza a triagem de vagas publicas para um perfil de engenharia, automacao e dados. Ele coleta oportunidades, calcula aderencia ao perfil, remove duplicatas, salva em SQLite, gera analise vaga x perfil e mostra tudo em um dashboard Streamlit. O projeto tambem inclui e-mail, agendamento no Windows, testes e cuidados para publicacao segura no GitHub.

## Explicacao tecnica de 2 minutos

O projeto foi construido em camadas. A primeira camada coleta vagas por uma fonte mock e por busca publica controlada, sem login, candidatura automatica ou bypass de bloqueios. Depois, um matcher calcula score com base em palavras-chave configuradas em YAML. As vagas sao persistidas em SQLite via SQLAlchemy, com deduplicacao por URL e por titulo, empresa e local.

Na etapa seguinte, criei um dashboard em Streamlit usando Pandas para filtros, metricas, graficos, exportacao CSV e visualizacao de analises. Tambem adicionei um comparador vaga x perfil baseado em regras locais, sem API externa, que gera fit score, fit level, skills encontradas, lacunas, riscos e mensagem sugerida para recrutador.

Para operacao, adicionei scripts Windows `.bat` com logs timestampados e documentacao para Task Scheduler. Para portfolio, criei dados ficticios, banco de exemplo, documentos de seguranca e checklist de publicacao.

## Decisoes de arquitetura

- SQLite para portabilidade e simplicidade local.
- YAML para separar perfil profissional do codigo.
- SQLAlchemy para modelagem e evolucao simples do banco.
- Streamlit para dashboard rapido e acessivel.
- Regras locais para analise, evitando dependencia de IA externa nesta fase.
- Scripts Windows para automacao compativel com o ambiente alvo.
- Dados ficticios separados para portfolio e screenshots.

## Desafios encontrados

- Manter o fluxo incremental sem quebrar funcionalidades anteriores.
- Criar score explicavel sem depender de dados sensiveis.
- Separar banco real e banco ficticio para publicacao segura.
- Preservar boas praticas: sem login automatizado, sem candidatura automatica e sem bypass de controles de acesso.

## Relacao com engenharia, automacao e dados

O projeto junta automacao de processos, organizacao de dados, analise de aderencia e visualizacao. Ele reflete um perfil hibrido de engenharia e dados: coleta informacao, estrutura em banco, transforma em indicadores e cria uma interface para decisao.

## Proximos passos

- Melhorar qualidade das fontes publicas.
- Integrar APIs oficiais quando disponiveis.
- Adicionar CI com GitHub Actions.
- Criar screenshots sanitizados.
- Evoluir para uma versao v1.0.0 com fluxo de favoritos e detalhes por vaga.
