from src.profile import load_profile


def test_load_profile_yaml(tmp_path):
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        """
desired_titles:
  - "Automation Engineer"
desired_locations:
  - "Campinas"
high_weight_keywords:
  - "Python"
medium_weight_keywords:
  - "dashboard"
negative_keywords:
  - "estagio"
priority_companies:
  - "Siemens"
min_score_to_email: 50
max_email_jobs: 3
""",
        encoding="utf-8",
    )

    profile = load_profile(profile_path)

    assert profile.desired_titles == ["Automation Engineer"]
    assert profile.desired_locations == ["Campinas"]
    assert profile.high_weight_keywords == ["Python"]
    assert profile.min_score_to_email == 50
    assert profile.max_email_jobs == 3
