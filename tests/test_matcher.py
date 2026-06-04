from src.models.job import JobListing
from src.profile import ProfileConfig
from src.services.matcher import JobMatcher


def make_profile() -> ProfileConfig:
    return ProfileConfig(
        high_weight_keywords=["automacao", "CLP", "Python", "engenharia de projetos"],
        medium_weight_keywords=["planejamento", "dashboard", "processos"],
        negative_keywords=["estagio", "telemarketing"],
        priority_companies=["Siemens"],
        min_score_to_email=50,
        max_email_jobs=5,
    )


def test_matcher_scores_strong_keywords_and_builds_reason():
    listing = JobListing(
        title="Engenheiro de Automacao",
        company="Siemens",
        location="Campinas",
        source="test",
        url="https://example.com/1",
        description_snippet="CLP, Python e engenharia de projetos industriais.",
    )

    scored = JobMatcher(make_profile()).score_listing(listing)

    assert scored.match_score >= 50
    assert scored.priority_company is True
    assert "Alta aderencia" in scored.match_reason
    assert "Python" in scored.match_reason


def test_matcher_penalizes_negative_keywords():
    result = JobMatcher(make_profile()).score_text(
        title="Estagio em Automacao",
        description="Vaga de estagio com telemarketing interno.",
    )

    assert result.score < 50
    assert "Baixa aderencia" in result.reason_text
    assert "estagio" in result.reason_text


def test_matcher_scores_medium_keywords():
    result = JobMatcher(make_profile()).score_text(
        title="Analista de Projetos",
        description="Planejamento, dashboard e processos.",
    )

    assert result.score > 0
    assert "Aderencia media" in result.reason_text


def test_matcher_does_not_match_keyword_inside_common_words():
    profile = ProfileConfig(high_weight_keywords=["ROS"])
    result = JobMatcher(profile).score_text(
        title="Produtor de Conteudo",
        description="Criacao de cursos e apoio aos nossos alunos.",
    )

    assert result.score == 0
    assert result.high_matches == []
