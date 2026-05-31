# Security Policy

## Dados que nao devem ser versionados

- `.env`
- `.venv/`
- `logs/`
- `data/jobs.db`
- logs reais
- bancos reais
- credenciais SMTP

## Principios do projeto

- Nao automatizar login.
- Nao automatizar candidatura.
- Nao burlar captcha.
- Nao ignorar bloqueios de acesso.
- Nao coletar dados sensiveis.
- Usar apenas dados publicos de vagas.
- Respeitar rate limit entre requisicoes.

## SMTP seguro

- Use senha de app quando disponivel.
- Nunca publique senha real.
- Teste primeiro com dry-run.
- Mantenha `EMAIL_DRY_RUN=true` ate validar o ambiente.
- Restrinja acesso local ao arquivo `.env`.

## Publicacao no GitHub

Antes de publicar:

1. Verifique `.gitignore`.
2. Remova bancos reais.
3. Remova logs reais.
4. Revise screenshots.
5. Use somente dados ficticios de `examples/` e `data/sample_jobs.db`.
6. Nunca publique e-mails pessoais, tokens, senhas ou URLs sensiveis.
