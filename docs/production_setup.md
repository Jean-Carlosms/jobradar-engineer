# Production Setup

Este guia prepara o JobRadar Engineer para uso recorrente com envio real de e-mail.

## Configurar `.env`

Copie o exemplo:

```bat
copy .env.example .env
```

Revise os campos:

```text
DATABASE_PATH=data/jobs.db
PROFILE_PATH=config/profile_keywords.yaml
PROFILE_SUMMARY_PATH=config/profile_summary.yaml
EMAIL_DRY_RUN=true
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=
EMAIL_TO=
AUTO_BACKUP_BEFORE_RUN=false
BACKUP_RETENTION_DAYS=30
```

Nao coloque credenciais reais em `.env.example`, README, TODO ou scripts.

## Dry-run vs envio real

Dry-run:

```bat
scripts\run_jobradar_dry_run.bat
```

Esse modo usa fonte mock, gera analise e registra o e-mail em log sem enviar.

Envio real:

```bat
scripts\run_jobradar_daily.bat
```

Esse modo usa `--send-email`. Ele depende de SMTP configurado corretamente no `.env`.

## Configurar SMTP

Campos comuns:

- `SMTP_HOST`: servidor SMTP do provedor.
- `SMTP_PORT`: normalmente `587` para STARTTLS ou `465` para SSL direto.
- `SMTP_USERNAME`: usuario/login do e-mail.
- `SMTP_PASSWORD`: senha ou App Password.
- `SMTP_USE_TLS`: `true` para STARTTLS, normalmente com porta `587`.
- `SMTP_USE_SSL`: `true` para SSL direto, normalmente com porta `465`.
- `EMAIL_FROM`: remetente.
- `EMAIL_TO`: destinatario.

Use apenas um modo criptografico por vez. Para porta `587`, use `SMTP_USE_TLS=true` e `SMTP_USE_SSL=false`. Para porta `465`, use `SMTP_USE_TLS=false` e `SMTP_USE_SSL=true`.

## Gmail App Password

Para Gmail, prefira App Password:

1. Ative verificacao em duas etapas na conta Google.
2. Acesse as configuracoes de seguranca da conta.
3. Crie uma senha de app para e-mail.
4. Use essa senha em `SMTP_PASSWORD`.
5. Nao use sua senha principal da conta.

Valores comuns para Gmail:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

Alternativa Gmail com SSL direto:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

## Testar antes de envio real

1. Rode `scripts\run_jobradar_dry_run.bat`.
2. Verifique o log em `logs/`.
3. Confira score minimo e analises.
4. Teste o alerta operacional com `python -m src.main --test-operational-alert --dry-run`.
5. Crie um backup manual com `python -m src.main --backup-db --backup-reason "antes do agendamento"`.
6. Configure SMTP no `.env`.
7. Rode manualmente `scripts\run_jobradar_daily.bat`.
8. Confirme o recebimento do e-mail.
9. So entao configure o Agendador de Tarefas.

## Backup do banco local

Antes de agendar execucoes diarias, crie um backup de `data/jobs.db`:

```bat
python -m src.main --backup-db --backup-reason "antes do agendamento diario"
python -m src.main --list-db-backups
```

Para habilitar backup automatico antes de cada execucao:

```text
AUTO_BACKUP_BEFORE_RUN=true
BACKUP_RETENTION_DAYS=30
```

`BACKUP_RETENTION_DAYS` fica documentado para politica futura; esta fase nao apaga backups automaticamente. Backups reais ficam em `backups/` e nao devem ser versionados.

Restaurar exige confirmacao explicita e cria backup automatico do estado atual antes de sobrescrever `data/jobs.db`:

```bat
python -m src.main --restore-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json --confirm-restore
```

Use `--verify-db-backup` antes de restaurar:

```bat
python -m src.main --verify-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json
```

Rotina recomendada:

- Antes do agendamento diario: habilite `AUTO_BACKUP_BEFORE_RUN=true`.
- Semanalmente: rode `python -m src.main --db-backup-summary`.
- Periodicamente: verifique um backup recente com `python -m src.main --verify-db-backup backups\jobs_backup_YYYYMMDD_HHMMSS.json`.
- Mensalmente: rode `python -m src.main --export-db-summary` e `python -m src.main --db-maintenance`.
- Antes e depois da manutencao: rode `python -m src.main --db-health`.
- Para auditoria: rode `python -m src.main --export-db-health`.
- Mensalmente: simule limpeza com `python -m src.main --cleanup-db-backups-dry-run`.
- Depois de revisar o relatorio, execute `python -m src.main --cleanup-db-backups --confirm-cleanup-backups` se quiser remover candidatos.
- No dashboard: use a aba `Backups e Banco` para visualizar manifestos e tamanhos, sem restaurar pelo painel.

## Migracao de schema

O projeto usa `schema_migrations` para controlar a versao local do schema SQLite, sem Alembic nesta fase. Antes de qualquer migracao manual em banco real, crie backup:

```bat
python -m src.main --backup-db --backup-reason "before schema migration"
python -m src.main --migrate-schema
python -m src.main --schema-status
```

Use `--schema-status` tambem depois de atualizar o projeto para confirmar se o banco esta na versao esperada.

## Saude do banco

Use os comandos de saude para acompanhar tamanho, integridade, versao de schema, tabelas, linhas, indices e freelist:

```bat
python -m src.main --db-health
python -m src.main --export-db-health
```

Rotina sugerida:

1. Rode `python -m src.main --db-health` antes de `--db-maintenance`.
2. Rode `python -m src.main --db-maintenance`.
3. Rode `python -m src.main --db-health` novamente.
4. Exporte evidencia com `python -m src.main --export-db-health`.

## Alertas operacionais

Alertas operacionais sao e-mails separados do e-mail de vagas. Eles usam o relatorio da execucao em `runs/` como base e ajudam a perceber falhas de fonte, execucoes sem vagas ou execucoes sem vagas elegiveis para envio.

Variaveis:

```text
OPERATIONAL_ALERTS_ENABLED=false
OPERATIONAL_ALERTS_ON_FAILURE=true
OPERATIONAL_ALERTS_ON_NO_JOBS=true
OPERATIONAL_ALERTS_ON_NO_EMAIL_ELIGIBLE=false
OPERATIONAL_DAILY_SUMMARY=false
```

Tipos:

- `failure`: fontes com erro.
- `no_jobs`: nenhuma vaga unica coletada.
- `no_email_eligible`: houve coleta, mas nada ficou elegivel para e-mail.
- `success_summary`: resumo opcional de uma execucao bem-sucedida.

Teste sem envio real:

```bat
python -m src.main --test-operational-alert --dry-run
python -m src.main --source mock --dry-run --run-report --send-operational-alerts
```

Ativar em producao:

1. Valide o SMTP com dry-run primeiro.
2. Configure `OPERATIONAL_ALERTS_ENABLED=true`.
3. Mantenha `OPERATIONAL_ALERTS_ON_FAILURE=true`.
4. Mantenha `OPERATIONAL_ALERTS_ON_NO_JOBS=true` se quiser aviso quando as fontes nao retornarem vagas.
5. Ative `OPERATIONAL_ALERTS_ON_NO_EMAIL_ELIGIBLE=true` apenas se esse volume de alerta fizer sentido.
6. Use `OPERATIONAL_DAILY_SUMMARY=true` somente se quiser resumo mesmo quando tudo funcionar.
7. Rode com `--run-report`, pois o alerta registra status no relatorio da execucao.

Para desativar em uma execucao especifica:

```bat
python -m src.main --source all --dry-run --run-report --no-operational-alerts
```

## Evitar spam

- Use `MIN_SCORE_TO_EMAIL` ou `--min-score` com valor conservador.
- Use `MAX_EMAIL_JOBS` para limitar o volume por execucao.
- Mantenha deduplicacao ativa pelo SQLite.
- Evite agendar varias execucoes no mesmo dia.
- Comece com fonte `mock` e dry-run para validar.

## Ajustar score minimo

Por linha de comando:

```bat
python -m src.main --source all --analyze --dry-run --min-score 60 --analysis-min-score 60
```

Pelo `.env`:

```text
MIN_SCORE_TO_EMAIL=60
```

Pelo perfil:

```text
config/profile_keywords.yaml
```

## Limpar banco local com seguranca

O banco local fica em:

```text
data/jobs.db
```

Para limpar:

1. Feche dashboard e execucoes em andamento.
2. Faca backup se quiser preservar historico.
3. Apague `data/jobs.db`.
4. Rode novamente o robo.

Isso remove historico de vagas, envios e analises.

## Limitacoes da busca publica

- Resultados podem variar por dia, regiao e mecanismo de busca.
- Algumas paginas podem exigir login ou captcha; o projeto nao tenta contornar isso.
- O snippet pode ser incompleto, afetando score e analise.
- Para producao robusta, prefira APIs publicas oficiais quando disponiveis.
