from __future__ import annotations

from src.models.job import JobListing
from src.sources.base import JobSource


class GupySource(JobSource):
    name = "GupySimulada"

    def fetch(self, keywords: list[str], locations: list[str]) -> list[JobListing]:
        return [
            JobListing(
                title="Engenheiro de Automacao Industrial",
                company="Empresa Industrial Exemplo",
                location="Campinas - Hibrido",
                source=self.name,
                url="https://jobs.example.com/gupy/engenheiro-automacao-industrial",
                description_snippet=(
                    "Atuacao com CLP Siemens, redes industriais, melhoria de processos, "
                    "Python para automacao e dashboards em Power BI."
                ),
                published_date="recente",
                query_used="mock:gupy:Engenheiro de Automacao:Campinas",
            ),
            JobListing(
                title="Manufacturing Engineer",
                company="Siemens",
                location="Sorocaba",
                source=self.name,
                url="https://jobs.example.com/gupy/manufacturing-engineer-sorocaba",
                description_snippet=(
                    "Projetos de manufatura, Industria 4.0, analise de dados, PLC Rockwell "
                    "e suporte tecnico para linhas automatizadas."
                ),
                published_date="recente",
                query_used="mock:gupy:Manufacturing Engineer:Sorocaba",
            ),
            JobListing(
                title="Vendedor Tecnico",
                company="Comercial Exemplo",
                location="Sao Paulo",
                source=self.name,
                url="https://jobs.example.com/gupy/vendedor-tecnico",
                description_snippet="Vaga comercial pura para vendas externas e prospeccao.",
                published_date="recente",
                query_used="mock:gupy:Vendedor Tecnico:Sao Paulo",
            ),
        ]
