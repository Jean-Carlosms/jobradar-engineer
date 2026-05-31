from src.models.job import Job
from src.profile_summary import ProfileSummary
from src.services.job_profile_analyzer import JobProfileAnalyzer


def make_summary() -> ProfileSummary:
    return ProfileSummary(
        core_skills=[
            "automacao industrial",
            "Python",
            "Power BI",
            "CLP Siemens",
            "CLP Rockwell",
            "Industria 4.0",
            "melhoria de processos",
            "robotica",
        ],
        tools=["Python", "Power BI", "Siemens TIA Portal", "Rockwell Studio 5000"],
        interest_areas=["automacao industrial", "dados industriais", "robotica"],
        target_roles=["Engenheiro de Automacao", "Automation Engineer"],
        target_companies=["Siemens"],
        strengths=["Perfil hibrido entre engenharia, automacao, dados e melhoria de processos."],
        current_gaps=["Cloud avancado."],
    )


def make_job(title: str, description: str, score: float = 80, company: str = "Siemens") -> Job:
    return Job(
        id=1,
        title=title,
        company=company,
        location="Campinas",
        source="mock",
        url="https://example.com/job",
        description_snippet=description,
        match_score=score,
        match_reason=description,
        priority_company=company == "Siemens",
        query_used="mock",
    )


def test_analyzer_high_fit_job():
    analysis = JobProfileAnalyzer(make_summary()).analyze(
        make_job(
            "Engenheiro de Automacao",
            "Automacao industrial com Python, Power BI, CLP Siemens, Industria 4.0 e melhoria de processos.",
        )
    )

    assert analysis.fit_level == "alto"
    assert analysis.fit_score >= 70
    assert "Python" in analysis.matched_skills
    assert "CLP Siemens" in analysis.matched_skills


def test_analyzer_low_fit_job_with_negative_terms():
    analysis = JobProfileAnalyzer(make_summary()).analyze(
        make_job(
            "Vendedor",
            "Comercial puro, telemarketing e prospeccao.",
            score=5,
            company="Comercial ACME",
        )
    )

    assert analysis.fit_level == "baixo"
    assert analysis.fit_score < 40
    assert analysis.missing_skills
    assert any("telemarketing" in risk for risk in analysis.risks)


def test_analyzer_missing_skills_are_reported():
    analysis = JobProfileAnalyzer(make_summary()).analyze(
        make_job("Analista de Dados", "Power BI e dashboards industriais.", score=35, company="ACME")
    )

    assert "Power BI" in analysis.matched_skills
    assert "CLP Siemens" in analysis.missing_skills
    assert analysis.resume_keywords
