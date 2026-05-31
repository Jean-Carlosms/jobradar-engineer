# Windows Task Scheduler

Este guia configura o JobRadar Engineer para rodar automaticamente no Windows.

## Pre-requisitos

1. Projeto em `C:\jobradar-engineer`.
2. Dependencias instaladas com `python -m pip install -r requirements.txt`.
3. `.env` configurado.
4. Teste manual concluido com `scripts\run_jobradar_dry_run.bat`.

## Criar tarefa diaria

1. Abra o menu Iniciar.
2. Pesquise por `Agendador de Tarefas`.
3. Clique em `Criar Tarefa Basica`.
4. Nome sugerido: `JobRadar Engineer Daily`.
5. Descricao sugerida: `Coleta, analisa e envia vagas aderentes ao perfil`.
6. Em disparador, escolha `Diariamente`.
7. Horario sugerido: `08:00`.
8. Em acao, escolha `Iniciar um programa`.
9. Em `Programa/script`, informe:

```text
C:\jobradar-engineer\scripts\run_jobradar_daily.bat
```

10. Em `Iniciar em`, informe:

```text
C:\jobradar-engineer
```

11. Conclua o assistente.

## Opcao de executar sem usuario logado

Em `Propriedades` da tarefa, guia `Geral`, voce pode marcar `Executar estando o usuario conectado ou nao`, se aplicavel ao seu Windows. Nesse modo, o Windows pode pedir sua senha de usuario. Garanta que o `.env` esteja acessivel somente ao seu usuario.

## Testar manualmente

Antes de ativar envio real, rode:

```bat
scripts\run_jobradar_dry_run.bat
```

Depois, no Agendador de Tarefas:

1. Selecione `Biblioteca do Agendador de Tarefas`.
2. Encontre `JobRadar Engineer Daily`.
3. Clique com o botao direito.
4. Escolha `Executar`.

## Consultar logs

Os scripts criam arquivos em:

```text
C:\jobradar-engineer\logs
```

Arquivos esperados:

- `jobradar_daily_YYYYMMDD_HHMMSS.log`
- `jobradar_dry_run_YYYYMMDD_HHMMSS.log`

Abra o log mais recente para verificar coleta, analise, envio de e-mail e eventuais erros.

## Desativar a tarefa

1. Abra o Agendador de Tarefas.
2. Encontre `JobRadar Engineer Daily`.
3. Clique com o botao direito.
4. Escolha `Desabilitar`.

Para remover definitivamente, escolha `Excluir`.

## Cuidados com credenciais

- Nunca coloque senha real em arquivos versionados.
- Guarde credenciais somente no `.env`.
- Use App Password quando o provedor de e-mail permitir.
- Mantenha `.env`, `.venv`, `logs/` e `data/jobs.db` fora do Git.
- Teste sempre com dry-run antes de ativar `--send-email`.
