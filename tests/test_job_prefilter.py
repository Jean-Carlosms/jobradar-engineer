from src.models.job import JobListing
from src.profile import ProfileConfig
from src.services.job_prefilter import JobPrefilter


def make_profile() -> ProfileConfig:
    return ProfileConfig(
        technical_title_keywords=["engenheiro", "automacao", "python", "dados"],
        technical_area_keywords=["CLP", "Power BI", "processos"],
        strong_negative_title_keywords=["estagio", "vendedor", "loja"],
        weak_negative_title_keywords=["assistente", "auxiliar", "comercial"],
        location_boost_keywords=["Sorocaba", "Campinas", "Remoto"],
        priority_companies=["Siemens"],
        priority_company_boost=10,
    )


def make_job(title: str, company: str = "Empresa", location: str = "Sao Paulo", description: str = "") -> JobListing:
    return JobListing(
        title=title,
        company=company,
        location=location,
        source="test",
        url=f"https://example.com/{title.replace(' ', '-').lower()}",
        description_snippet=description,
    )


def test_prefilter_keeps_technical_job():
    result = JobPrefilter(make_profile()).evaluate(
        make_job("Engenheiro de Automacao", description="Projetos com CLP e Power BI.")
    )

    assert result.should_keep is True
    assert result.should_enrich is True
    assert result.prefilter_score > 0
    assert "termos tecnicos" in result.prefilter_reason


def test_prefilter_discards_strong_commercial_job():
    result = JobPrefilter(make_profile()).evaluate(make_job("Vendedor de Loja"))

    assert result.should_keep is False
    assert result.should_enrich is False
    assert "negativo forte" in result.prefilter_reason


def test_prefilter_discards_internship_without_technical_signal():
    result = JobPrefilter(make_profile()).evaluate(make_job("Estagio Administrativo"))

    assert result.should_keep is False
    assert "estagio" in result.prefilter_reason


def test_prefilter_priority_company_gets_bonus():
    matcher = JobPrefilter(make_profile())
    base = matcher.evaluate(make_job("Engenheiro de Dados", company="Empresa"))
    priority = matcher.evaluate(make_job("Engenheiro de Dados", company="Siemens"))

    assert priority.prefilter_score > base.prefilter_score
    assert priority.priority_company is True


def test_prefilter_desired_location_gets_bonus():
    matcher = JobPrefilter(make_profile())
    base = matcher.evaluate(make_job("Engenheiro de Dados", location="Curitiba"))
    boosted = matcher.evaluate(make_job("Engenheiro de Dados", location="Campinas"))

    assert boosted.prefilter_score > base.prefilter_score
    assert boosted.location_matches == ["Campinas"]


def test_prefilter_weak_negative_does_not_always_discard():
    result = JobPrefilter(make_profile()).evaluate(make_job("Assistente de Dados", description="Power BI e processos."))

    assert result.should_keep is True
    assert result.should_enrich is False
    assert "negativo fraco" in result.prefilter_reason


def test_prefilter_results_sort_by_score():
    matcher = JobPrefilter(make_profile())
    jobs = [
        make_job("Auxiliar Administrativo"),
        make_job("Engenheiro de Automacao", location="Campinas", description="CLP."),
        make_job("Analista Python Dados", company="Siemens", location="Remoto", description="Power BI."),
    ]

    ranked = sorted(
        ((matcher.evaluate(job), job) for job in jobs),
        key=lambda item: item[0].prefilter_score,
        reverse=True,
    )

    assert ranked[0][1].title == "Analista Python Dados"
    assert ranked[-1][1].title == "Auxiliar Administrativo"
