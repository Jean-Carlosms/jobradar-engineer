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
4. Configure SMTP no `.env`.
5. Rode manualmente `scripts\run_jobradar_daily.bat`.
6. Confirme o recebimento do e-mail.
7. So entao configure o Agendador de Tarefas.

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
