from src.profile_summary import load_profile_summary


def test_load_profile_summary_yaml(tmp_path):
    profile_path = tmp_path / "profile_summary.yaml"
    profile_path.write_text(
        """
professional_summary: "Engenheiro mecatronico com automacao e dados."
core_skills:
  - "Python"
  - "CLP Siemens"
tools:
  - "Power BI"
interest_areas:
  - "Industria 4.0"
target_roles:
  - "Automation Engineer"
target_companies:
  - "Siemens"
strengths:
  - "Perfil hibrido entre engenharia e dados."
current_gaps:
  - "Cloud avancado."
languages:
  - "Portugues nativo"
location_preferences:
  - "Campinas"
""",
        encoding="utf-8",
    )

    profile = load_profile_summary(profile_path)

    assert profile.professional_summary.startswith("Engenheiro")
    assert profile.core_skills == ["Python", "CLP Siemens"]
    assert profile.target_companies == ["Siemens"]
    assert profile.location_preferences == ["Campinas"]
