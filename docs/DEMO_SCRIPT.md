# Demo Script - JobRadar Engineer em 3 minutos

Use este roteiro para demonstrar o projeto com dados ficticios, sem expor informacoes reais.

## Preparacao

```bat
python scripts\load_sample_data.py
streamlit run dashboard.py
```

No dashboard, selecione `Dados ficticios`.

## Roteiro de 3 minutos

1. Abra o dashboard e explique o objetivo: reduzir tempo de triagem de vagas tecnicas com um pipeline local.
2. Mostre `Resumo Executivo`: total de vagas, match medio, vagas analisadas e revisadas.
3. Mostre `Funil de Vagas`: Coleta -> Pre-filtro -> Match -> Analise -> Revisao.
4. Abra `Top Vagas`: destaque uma vaga com alto match e empresa/localidade relevantes.
5. Va para `Analise Vaga x Perfil`: mostre fit score, competencias encontradas, lacunas e mensagem sugerida.
6. Va para `Revisao Humana`: explique status, favorita e observacoes para calibrar o perfil.
7. Va para `Insights de Feedback`: mostre como revisoes humanas viram sinais para ajustes manuais.
8. Mostre `Historico de Execucoes`: execucoes anteriores, duracao, erros e e-mails.
9. Mostre `Alertas Operacionais`: falhas, zero vagas e alertas gerados a partir de `runs/*.json`.
10. Mostre `Backups e Banco`: backups, comandos de manutencao e `Saude do Banco`.
11. Feche com seguranca e compliance: sem login, sem candidatura automatica, sem bypass de captcha e sem dados sensiveis versionados.

## Roteiro com screenshots

1. Imagem 1: `docs/images/dashboard-overview.png` - aba `Resumo Executivo`.
2. Imagem 2: `docs/images/job-funnel.png` - aba `Funil de Vagas`.
3. Imagem 3: `docs/images/top-jobs.png` - aba `Top Vagas`.
4. Imagem 4: `docs/images/job-profile-analysis.png` - aba `Analise Vaga x Perfil`.
5. Imagem 5: `docs/images/human-review.png` - aba `Revisao Humana`.
6. Imagem 6: `docs/images/prefilter-audit.png` - aba `Auditoria do Pre-filtro`.
7. Imagem 7: `docs/images/feedback-insights.png` - aba `Insights de Feedback`.

Todos os screenshots publicos devem usar `Dados ficticios`.

## Frase curta de fechamento

O JobRadar Engineer transforma coleta publica de vagas em um fluxo local auditavel: coleta, pre-filtra, pontua, analisa, permite revisao humana e gera sinais para calibragem sem alterar configuracoes automaticamente.

Na versao v3.0.0, a demo tambem mostra operacao local completa: historico de execucoes, alertas operacionais, backups, schema versionado e saude do banco.

## Cuidados durante a demo

- Use apenas `Dados ficticios`.
- Nao abra `.env`, logs reais, banco real ou relatorios reais.
- Nao mostre e-mail, credenciais, caminhos locais sensiveis ou URLs privadas.
- Nao execute candidatura automatica; o projeto nao faz isso.
