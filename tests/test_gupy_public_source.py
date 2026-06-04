import csv

import requests

from src.config import Settings
from src.gupy_companies import GupyCompany
from src.models.job import JobListing
from src.profile import ProfileConfig
from src.sources.gupy_source import GupyCompanyRunStatus, GupyExtractedJob, GupyJobDetailParser, GupyPublicSource


class FakeResponse:
    def __init__(self, url: str, text: str, status_code: int = 200) -> None:
        self.url = url
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def make_source(tmp_path, companies=None, debug_search=False, profile=None, **settings_kwargs):
    settings = Settings(
        project_root=tmp_path,
        rate_limit_seconds=0,
        request_timeout_seconds=1,
        gupy_detail_request_delay_seconds=0,
        **settings_kwargs,
    )
    return GupyPublicSource(settings, companies=companies, profile=profile, debug_search=debug_search)


def make_company() -> GupyCompany:
    return GupyCompany(name="Facens", slug="facens", base_url="https://facens.gupy.io")


def test_gupy_parser_extracts_jobs_links_from_html(tmp_path):
    source = make_source(tmp_path)
    company = make_company()
    html = """
    <ul>
      <li><a href="/jobs/123">Engenheiro de Automacao - Campinas</a></li>
      <li><a href="https://facens.gupy.io/jobs/456">Analista de Projetos - Sorocaba</a></li>
    </ul>
    """

    jobs = source.parse_html_links(html, company=company, page_url="https://facens.gupy.io/jobs")

    assert len(jobs) == 2
    assert jobs[0].title.startswith("Engenheiro")
    assert jobs[0].company == "Facens"
    assert jobs[0].location == "Campinas"
    assert jobs[0].url == "https://facens.gupy.io/jobs/123"


def test_gupy_parser_extracts_jobs_from_embedded_json(tmp_path):
    source = make_source(tmp_path)
    company = make_company()
    html = """
    <script type="application/json">
    {"jobs":[{"title":"Manufacturing Engineer","url":"/jobs/789","location":"Sorocaba","description":"Industria 4.0"}]}
    </script>
    """

    jobs = source.parse_embedded_json(html, company=company, page_url="https://facens.gupy.io/jobs")

    assert len(jobs) == 1
    assert jobs[0].title == "Manufacturing Engineer"
    assert jobs[0].location == "Sorocaba"
    assert jobs[0].url == "https://facens.gupy.io/jobs/789"


def test_gupy_json_location_dict_is_formatted(tmp_path):
    source = make_source(tmp_path)
    company = make_company()
    html = """
    <script type="application/json">
    {"jobs":[{"title":"Analista Senior","url":"/jobs/790","location":{"address":{"city":"Sorocaba","stateShortName":"SP"},"workplaceType":"on-site"}}]}
    </script>
    """

    jobs = source.parse_embedded_json(html, company=company, page_url="https://facens.gupy.io/jobs")

    assert jobs[0].location == "Sorocaba - SP - on-site"


def test_gupy_source_deduplicates_inside_source(tmp_path):
    source = make_source(tmp_path)
    company = make_company()
    html = """
    <a href="/jobs/123">Engenheiro de Automacao - Campinas</a>
    <a href="https://facens.gupy.io/jobs/123">Engenheiro de Automacao - Campinas</a>
    """

    jobs = source.parse_html_links(html, company=company, page_url="https://facens.gupy.io/jobs")
    listings = source._deduplicate_jobs(
        [
            JobListing(
                title=job.title,
                company=job.company,
                location=job.location,
                source=source.name,
                url=job.url,
            )
            for job in jobs
        ]
    )

    assert len(listings) == 1


def test_gupy_source_deduplicates_job_urls_with_query_string(tmp_path):
    source = make_source(tmp_path)
    listings = source._deduplicate_jobs(
        [
            JobListing(
                title="Produtor de Conteudo",
                company="Facens",
                location="Sorocaba",
                source=source.name,
                url="https://facens.gupy.io/jobs/11325049?jobBoardSource=gupy_public_page",
            ),
            JobListing(
                title="Produtor de Conteudo",
                company="Facens",
                location="Sorocaba - SP - on-site",
                source=source.name,
                url="https://facens.gupy.io/jobs/11325049",
            ),
        ]
    )

    assert len(listings) == 1


def test_gupy_fetch_continues_when_company_fails(tmp_path, monkeypatch):
    good = GupyCompany(name="Good", slug="good", base_url="https://good.gupy.io")
    bad = GupyCompany(name="Bad", slug="bad", base_url="https://bad.gupy.io")
    source = make_source(tmp_path, companies=[bad, good])

    def fake_fetch_company(company, status=None):
        if company.slug == "bad":
            raise requests.RequestException("network error")
        return [
            GupyExtractedJob(
                title="Automation Engineer",
                company=company.name,
                location="Campinas",
                url="https://good.gupy.io/jobs/1",
                description_snippet="Python",
                query_used="test",
            )
        ]

    monkeypatch.setattr(source, "_fetch_company", fake_fetch_company)

    jobs = source.fetch([], [])

    assert len(jobs) == 1
    assert jobs[0].company == "Good"


def test_gupy_invalid_company_does_not_break_execution(tmp_path, monkeypatch):
    invalid = GupyCompany(
        name="Invalid",
        slug="invalid",
        base_url="https://invalid.gupy.io",
        category="industry_manufacturing",
        priority=True,
        status="invalid_slug",
        notes="Expected to fail in this test.",
    )
    valid = GupyCompany(name="Valid", slug="valid", base_url="https://valid.gupy.io")
    source = make_source(tmp_path, companies=[invalid, valid], gupy_enrich_details=False)

    def fake_get(url):
        if "invalid" in url:
            return FakeResponse(url, "<html>not found</html>", status_code=404)
        return FakeResponse(url, '<a href="/jobs/1">Automation Engineer - Campinas</a>', status_code=200)

    monkeypatch.setattr(source, "_get", fake_get)

    jobs = source.fetch([], [])

    assert len(jobs) == 1
    assert jobs[0].company == "Valid"
    assert source.company_statuses[0].status_http == 404
    assert source.company_statuses[0].error
    assert source.company_statuses[1].jobs_created >= 1


def test_gupy_source_applies_prefilter_before_enrichment(tmp_path, monkeypatch):
    company = GupyCompany(name="Facens", slug="facens", base_url="https://facens.gupy.io", priority=True)
    profile = ProfileConfig(
        technical_title_keywords=["engenheiro", "automacao"],
        strong_negative_title_keywords=["vendedor"],
        location_boost_keywords=["Campinas"],
        priority_company_boost=10,
    )
    source = make_source(tmp_path, companies=[company], profile=profile, gupy_max_detail_pages=1)

    html = """
    <a href="/jobs/1">Engenheiro de Automacao - Campinas</a>
    <a href="/jobs/2">Vendedor de Loja</a>
    """
    calls = []

    def fake_get(url):
        calls.append(url)
        if "/jobs/1" in url:
            return FakeResponse(url, "<h1>Engenheiro de Automacao</h1><section><h2>Descricao</h2><p>CLP e Python.</p></section>")
        return FakeResponse(url, html)

    monkeypatch.setattr(source, "_get", fake_get)

    jobs = source.fetch([], [])

    assert len(jobs) == 1
    assert jobs[0].title == "Engenheiro de Automacao"
    assert jobs[0].prefilter_score > 0
    assert "manter" in jobs[0].prefilter_reason
    assert any("/jobs/1" in call for call in calls)
    assert not any("/jobs/2" in call for call in calls)


def test_gupy_company_status_report_is_written(tmp_path):
    source = make_source(tmp_path, debug_search=True)
    statuses = [
        GupyCompanyRunStatus(
            name="Facens",
            slug="facens",
            base_url="https://facens.gupy.io",
            category="education_research",
            priority=True,
            configured_status="active",
            notes="Test",
            status_http=200,
            jobs_found=2,
            jobs_created=2,
            error="",
        )
    ]

    path = source._write_company_status_report(statuses)

    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["name"] == "Facens"
    assert rows[0]["category"] == "education_research"
    assert rows[0]["status_http"] == "200"
    assert rows[0]["jobs_created"] == "2"


def test_gupy_prefilter_debug_report_is_written(tmp_path):
    profile = ProfileConfig(technical_title_keywords=["engenheiro"], location_boost_keywords=["Campinas"])
    source = make_source(tmp_path, debug_search=True, profile=profile)
    job = JobListing("Engenheiro de Dados", "Facens", "Campinas", source.name, "https://facens.gupy.io/jobs/1")
    evaluated = source._apply_prefilter(
        [job],
        {source._canonical_job_key(job.url): {"category": "education_research", "priority": True}},
    )[2]

    path = source._write_prefilter_debug_file(evaluated)

    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["title"] == "Engenheiro de Dados"
    assert rows[0]["should_keep"] == "True"
    assert rows[0]["should_enrich"] == "True"


def test_gupy_debug_writes_files(tmp_path):
    source = make_source(tmp_path, debug_search=True)
    company = make_company()

    source._write_debug_files(company, "https://facens.gupy.io/jobs", "<html></html>", ["Job -> https://facens.gupy.io/jobs/1"])

    debug_dir = tmp_path / "logs" / "gupy_debug"
    assert list(debug_dir.glob("*_sample.html"))
    assert list(debug_dir.glob("*_links.txt"))


def test_gupy_detail_parser_extracts_detail_html():
    parser = GupyJobDetailParser()
    html = """
    <html>
      <h1>Engenheiro de Automacao Pleno</h1>
      <section><h2>Descricao da vaga</h2><p>Atuar com automacao industrial e Python.</p></section>
      <section><h2>Responsabilidades</h2><p>Desenvolver melhorias em CLP Siemens.</p></section>
      <section><h2>Requisitos</h2><p>Experiencia com Power BI e redes industriais.</p></section>
      <section><h2>Beneficios</h2><p>Vale refeicao e plano de saude.</p></section>
      <p>Sorocaba - SP Presencial Publicada em 2026-05-30</p>
    </html>
    """

    detail = parser.parse(html, fallback_url="https://facens.gupy.io/jobs/123")

    assert detail.title == "Engenheiro de Automacao Pleno"
    assert "automacao industrial" in detail.description
    assert "CLP Siemens" in detail.responsibilities
    assert "Power BI" in detail.requirements
    assert detail.job_id == "123"
    assert "Vale refeicao" in detail.aggregated_text


def test_gupy_detail_parser_extracts_detail_json():
    parser = GupyJobDetailParser()
    html = """
    <script type="application/json">
    {"job":{"title":"Automation Engineer","description":"Python e PLC","requirements":"Ingles tecnico","benefits":"Bonus","location":{"address":{"city":"Campinas","stateShortName":"SP"},"workplaceType":"hybrid"},"id":999}}
    </script>
    """

    detail = parser.parse(html, fallback_url="https://company.gupy.io/jobs/999")

    assert detail.title == "Automation Engineer"
    assert detail.location == "Campinas - SP - hybrid"
    assert detail.description == "Python e PLC"
    assert detail.requirements == "Ingles tecnico"
    assert detail.job_id == "999"


def test_gupy_enrichment_updates_description_and_respects_limit(tmp_path, monkeypatch):
    source = make_source(tmp_path, gupy_max_detail_pages=1)
    jobs = [
        JobListing("Vaga 1", "Facens", "Nao identificado", "GupyPublic", "https://facens.gupy.io/jobs/1", "Curto"),
        JobListing("Vaga 2", "Facens", "Nao identificado", "GupyPublic", "https://facens.gupy.io/jobs/2", "Curto"),
    ]
    calls = []

    def fake_get(url):
        calls.append(url)
        return FakeResponse(
            url,
            """
            <h1>Vaga enriquecida</h1>
            <section><h2>Descricao da vaga</h2><p>Texto longo com Python, CLP Siemens e Power BI.</p></section>
            <p>Sorocaba - SP</p>
            """,
        )

    monkeypatch.setattr(source, "_get", fake_get)

    enriched = source.enrich_job_details(jobs)

    assert len(calls) == 1
    assert enriched[0].title == "Vaga enriquecida"
    assert "Python" in enriched[0].description_snippet
    assert enriched[1].description_snippet == "Curto"


def test_gupy_enrichment_does_not_replace_known_company_with_detail_noise(tmp_path, monkeypatch):
    source = make_source(tmp_path, gupy_max_detail_pages=1)
    job = JobListing("Vaga", "Facens", "Nao identificado", "GupyPublic", "https://facens.gupy.io/jobs/1", "Curto")

    monkeypatch.setattr(
        source,
        "_get",
        lambda url: FakeResponse(
            url,
            """
            <script type="application/json">
            {"job":{"title":"Vaga","company":"America/Sao_Paulo gruposplice pt","description":"Python"}}
            </script>
            """,
        ),
    )

    enriched = source.enrich_job_details([job])

    assert enriched[0].company == "Facens"


def test_gupy_enrichment_preserves_basic_job_when_detail_fails(tmp_path, monkeypatch):
    source = make_source(tmp_path, gupy_max_detail_pages=1)
    job = JobListing("Vaga basica", "Facens", "Sorocaba", "GupyPublic", "https://facens.gupy.io/jobs/1", "Resumo basico")

    def fake_get(url):
        raise requests.RequestException("timeout")

    monkeypatch.setattr(source, "_get", fake_get)

    enriched = source.enrich_job_details([job])

    assert enriched[0].title == "Vaga basica"
    assert enriched[0].description_snippet == "Resumo basico"


def test_gupy_detail_debug_writes_files(tmp_path, monkeypatch):
    source = make_source(tmp_path, debug_search=True, gupy_max_detail_pages=1)
    job = JobListing("Vaga", "Facens", "Sorocaba", "GupyPublic", "https://facens.gupy.io/jobs/1", "Resumo")

    monkeypatch.setattr(
        source,
        "_get",
        lambda url: FakeResponse(url, "<h1>Vaga</h1><section><h2>Descricao</h2><p>Python</p></section>"),
    )

    source.enrich_job_details([job])

    debug_dir = tmp_path / "logs" / "gupy_debug"
    assert list(debug_dir.glob("*_detail.txt"))
    assert list(debug_dir.glob("*_sample.html"))
