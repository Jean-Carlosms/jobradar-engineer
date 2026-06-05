# Coverage Review v2.8.0

Este documento registra a decisao arquitetural para modulos com cobertura baixa ou com papel experimental. A revisao usa como base a execucao:

```bat
python -m pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=85
```

Cobertura total de referencia: aproximadamente `89%`.

## Decisoes

| Modulo | Cobertura aprox. | Importancia | Papel no projeto | Decisao | Acao recomendada | Prioridade |
| --- | ---: | --- | --- | --- | --- | --- |
| `src/sources/search_engine_source.py` | 67% | util | Fallback experimental por busca publica HTML | Manter documentado como fallback | Preferir GupyPublic para uso real; cobrir apenas parser, challenge, fallback e filtros; avaliar API oficial no futuro | media |
| `src/services/scheduler.py` | 64% | util | Utilitario para agendamento local/Windows | Manter como utilitario pequeno | Teste minimo com scheduler fake; sem refatoracao nesta fase | baixa |
| `src/sources/glassdoor_source.py` | 0% antes da fase | placeholder | Wrapper experimental de `SearchEngineSource` com filtro de dominio | Manter como contrato futuro documentado | Docstring e teste minimo de nome/filtro; avaliar remocao se nao houver uso futuro | baixa |
| `src/sources/indeed_source.py` | 0% antes da fase | placeholder | Wrapper experimental de `SearchEngineSource` com filtro de dominio | Manter como contrato futuro documentado | Docstring e teste minimo de nome/filtro; avaliar remocao se nao houver uso futuro | baixa |
| `src/sources/infojobs_source.py` | 0% antes da fase | placeholder | Wrapper experimental de `SearchEngineSource` com filtro de dominio | Manter como contrato futuro documentado | Docstring e teste minimo de nome/filtro; avaliar remocao se nao houver uso futuro | baixa |
| `src/sources/linkedin_source.py` | 0% antes da fase | placeholder | Wrapper experimental de `SearchEngineSource` com filtro de dominio | Manter como contrato futuro documentado | Docstring e teste minimo de nome/filtro; avaliar remocao se nao houver uso futuro | baixa |
| `src/main.py` | 83% | critico | CLI e orquestracao operacional | Manter e expandir testes por comportamento | Cobrir apenas branches de CLI/operacao relevantes; evitar testes artificiais | alta |
| `src/services/run_history.py` | 85% | util | Historico operacional para dashboard e CLI | Manter | Cobrir novos filtros e formatos quando surgirem | media |

## BuscaPublica

`SearchEngineSource` depende de HTML de buscador publico. Esse HTML pode mudar sem aviso, retornar challenge/captcha, limitar resultados ou ocultar links. Por isso, a decisao e manter a fonte como fallback experimental e diagnostico, nao como fonte primaria de producao.

Testes existentes e adicionados cobrem:

- parser de resultado HTML;
- fallback para links simples `a[href]`;
- limpeza de URLs redirecionadas por DuckDuckGo;
- filtro de dominio permitido;
- pagina de challenge/captcha;
- fallback sem links;
- erro de request sem quebrar a execucao;
- escrita de arquivos debug sanitizados.

## Scheduler

`scheduler.py` continua util para execucao local com `--schedule`, mas nao e o caminho principal do CI nem dos testes offline. A decisao e manter o modulo como utilitario pequeno, testado com scheduler fake para validar `timezone`, cron, hora, minuto e chamada de `start()`.

## Fontes Placeholder

As fontes `GlassdoorSource`, `IndeedSource`, `InfoJobsSource` e `LinkedInSource` sao wrappers experimentais de busca publica com filtro de dominio. Elas nao fazem login, nao burlam captcha e nao automatizam candidatura.

Decisao atual:

- manter como contrato futuro documentado;
- adicionar docstrings claras;
- cobrir nome/filtro por teste minimo;
- reavaliar remocao se nao houver uso real apos uma integracao via API oficial ou fonte dedicada.

## Recomendacao

Nao subir o limite para `90%` ainda. Antes disso, priorizar:

- melhorar `search_engine_source.py` apenas onde houver comportamento estavel;
- avaliar remocao ou promocao das fontes placeholder;
- considerar API oficial/opcional de busca para substituir dependencias de HTML de buscador;
- manter `GupyPublicSource` como fonte real principal.
