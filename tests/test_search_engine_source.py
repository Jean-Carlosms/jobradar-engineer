from src.config import Settings
from src.sources.glassdoor_source import GlassdoorSource
from src.sources.indeed_source import IndeedSource
from src.sources.infojobs_source import InfoJobsSource
from src.sources.linkedin_source import LinkedInSource
import src.sources.search_engine_source as search_module
from src.sources.search_engine_source import SearchEngineSource


def make_source(tmp_path, debug_search: bool = False) -> SearchEngineSource:
    settings = Settings(project_root=tmp_path, rate_limit_seconds=0, max_search_queries=20)
    return SearchEngineSource(settings, debug_search=debug_search)


def test_duckduckgo_parser_extracts_result_a_links(tmp_path):
    source = make_source(tmp_path)
    html = """
    <div class="result">
      <a class="result__a" href="https://empresa.gupy.io/jobs/123">Engenheiro de Automacao</a>
      <a class="result__snippet">Python, CLP Siemens e Power BI.</a>
    </div>
    """

    links = source.extract_links(html)
    filtered = source.filter_links(links)

    assert len(links) == 1
    assert len(filtered) == 1
    assert filtered[0].title == "Engenheiro de Automacao"
    assert filtered[0].url == "https://empresa.gupy.io/jobs/123"


def test_parser_fallback_extracts_all_href_links(tmp_path):
    source = make_source(tmp_path)
    html = '<html><body><a href="https://www.vagas.com.br/vagas/456">Automation Engineer</a></body></html>'

    links = source.extract_links(html)

    assert len(links) == 1
    assert links[0].selector == "a[href]"
    assert links[0].url == "https://www.vagas.com.br/vagas/456"


def test_clean_result_url_extracts_duckduckgo_uddg_target(tmp_path):
    source = make_source(tmp_path)
    raw_url = (
        "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.linkedin.com%2Fjobs%2Fview%2F123"
        "&rut=abc"
    )

    assert source.clean_result_url(raw_url) == "https://www.linkedin.com/jobs/view/123"


def test_domain_filter_accepts_target_job_sites(tmp_path):
    source = make_source(tmp_path)

    assert source.is_accepted_url("https://company.gupy.io/jobs/123")
    assert source.is_accepted_url("https://br.linkedin.com/jobs/view/123")
    assert source.is_accepted_url("https://www.catho.com.br/vagas/engenheiro")
    assert not source.is_accepted_url("https://example.com/jobs/123")


def test_links_to_jobs_uses_not_identified_defaults(tmp_path):
    source = make_source(tmp_path)
    html = '<a href="https://www.indeed.com/viewjob?jk=abc">Manufacturing Engineer</a>'
    links = source.filter_links(source.extract_links(html))

    jobs = source.links_to_jobs(links, query='"Manufacturing Engineer" Sorocaba', location="")

    assert len(jobs) == 1
    assert jobs[0].company == "Indeed"
    assert jobs[0].location == "Nao identificado"
    assert jobs[0].description_snippet


def test_debug_search_writes_files_for_html_sample(tmp_path):
    source = make_source(tmp_path, debug_search=True)
    html = '<a href="https://www.infojobs.com.br/vaga.aspx?id=1">Analista de Projetos</a>'
    links = source.extract_links(html)
    filtered = source.filter_links(links)
    jobs = source.links_to_jobs(filtered, query="Analista de Projetos Sorocaba", location="Sorocaba")

    source._write_debug_files(
        1,
        "Analista de Projetos Sorocaba",
        "https://html.duckduckgo.com",
        html,
        links,
        filtered,
        jobs,
        challenge_detected=False,
    )

    debug_dir = tmp_path / "logs" / "search_debug"
    assert list(debug_dir.glob("*_sample.html"))
    assert list(debug_dir.glob("*_links.txt"))


def test_detects_duckduckgo_challenge_page(tmp_path):
    source = make_source(tmp_path)
    html = """
    <div class="anomaly-modal">
      Unfortunately, bots use DuckDuckGo too.
      Please complete the following challenge to confirm this search was made by a human.
    </div>
    """

    assert source.detect_search_challenge(html) is True


def test_search_fetch_returns_empty_when_web_search_disabled(tmp_path):
    settings = Settings(project_root=tmp_path, enable_web_search=False)
    source = SearchEngineSource(settings)

    assert source.fetch(["Automation Engineer"], ["Campinas"]) == []


def test_search_duckduckgo_returns_empty_for_challenge_without_links(monkeypatch, tmp_path):
    class DummyResponse:
        url = "https://html.duckduckgo.com/html/"
        status_code = 200
        text = "<html><body>captcha complete the following challenge</body></html>"

        def raise_for_status(self):
            return None

    source = make_source(tmp_path)
    monkeypatch.setattr(search_module.requests, "get", lambda *args, **kwargs: DummyResponse())

    jobs = source._search_duckduckgo("site:gupy.io/jobs automacao", "Campinas")

    assert jobs == []


def test_search_fetch_continues_when_request_fails(monkeypatch, tmp_path):
    settings = Settings(project_root=tmp_path, rate_limit_seconds=0, max_search_queries=1)
    source = SearchEngineSource(settings)

    def raise_request_error(*args, **kwargs):
        raise search_module.requests.RequestException("falha simulada")

    monkeypatch.setattr(search_module.requests, "get", raise_request_error)

    assert source.fetch(["Automation Engineer"], ["Campinas"]) == []


def test_placeholder_sources_are_experimental_search_wrappers(tmp_path):
    settings = Settings(project_root=tmp_path, rate_limit_seconds=0)

    sources = [
        GlassdoorSource(settings),
        IndeedSource(settings),
        InfoJobsSource(settings),
        LinkedInSource(settings),
    ]

    assert [source.name for source in sources] == [
        "GlassdoorBuscaPublica",
        "IndeedBuscaPublica",
        "InfoJobsBuscaPublica",
        "LinkedInBuscaPublica",
    ]
    assert [source.search_sites for source in sources] == [
        ["glassdoor.com.br"],
        ["br.indeed.com"],
        ["infojobs.com.br"],
        ["linkedin.com/jobs/view"],
    ]
    assert all("Experimental public-search fallback" in (source.__class__.__doc__ or "") for source in sources)
