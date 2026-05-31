# Screenshots Guide

Use este guia para preparar imagens futuras do projeto para GitHub, portfolio e apresentacoes.

## Prints sugeridos

- Dashboard principal com metricas gerais.
- Filtros laterais.
- Tabela de vagas.
- Secao Top Vagas.
- Secao Empresas Prioritarias.
- Secao Analise Vaga x Perfil.
- Graficos por fonte, localidade, score e empresa.
- E-mail dry-run ou exemplo sanitizado.
- Logs sanitizados.

## Cuidados obrigatorios

- Nao expor e-mail real.
- Nao expor credenciais.
- Nao expor banco real.
- Nao expor links sensiveis.
- Nao expor logs reais com dados pessoais ou tokens.
- Usar dados ficticios ou sanitizados.
- Preferir `data/sample_jobs.db` para prints publicos.

## Fluxo recomendado

1. Gere o banco ficticio:

```bat
python scripts\load_sample_data.py
```

2. Abra o dashboard:

```bat
scripts\open_dashboard.bat
```

3. No seletor de banco, escolha `Dados ficticios`.
4. Tire os prints.
5. Salve as imagens em `docs/images/`.

Antes de publicar, revise cada imagem manualmente.
