from src.gupy_companies import load_gupy_companies


def test_load_gupy_companies_yaml(tmp_path):
    path = tmp_path / "gupy_companies.yaml"
    path.write_text(
        """
companies:
  - name: Facens
    slug: facens
    base_url: https://facens.gupy.io
""",
        encoding="utf-8",
    )

    companies = load_gupy_companies(path)

    assert len(companies) == 1
    assert companies[0].name == "Facens"
    assert companies[0].base_url == "https://facens.gupy.io"
    assert companies[0].category == "uncategorized"
    assert companies[0].priority is False
    assert companies[0].status == "unknown"


def test_load_gupy_companies_categorized_yaml(tmp_path):
    path = tmp_path / "gupy_companies.yaml"
    path.write_text(
        """
categories:
  industry_manufacturing:
    - name: Raizen
      slug: raizen
      base_url: https://raizen.gupy.io
      priority: true
      status: unknown
      notes: Energia e industria.
  technology_data:
    - name: Stone
      slug: stone
      base_url: https://stone.gupy.io
      priority: false
""",
        encoding="utf-8",
    )

    companies = load_gupy_companies(path)

    assert [company.name for company in companies] == ["Raizen", "Stone"]
    assert companies[0].category == "industry_manufacturing"
    assert companies[0].priority is True
    assert companies[0].notes == "Energia e industria."
    assert companies[1].category == "technology_data"
    assert companies[1].status == "unknown"


def test_load_gupy_companies_accepts_flat_and_categorized_yaml(tmp_path):
    path = tmp_path / "gupy_companies.yaml"
    path.write_text(
        """
companies:
  - name: Facens
    slug: facens
    base_url: https://facens.gupy.io
    category: education_research
    priority: yes
categories:
  logistics_mobility:
    - name: Localiza
      slug: localiza
      base_url: https://localiza.gupy.io
      notes: Mobilidade.
""",
        encoding="utf-8",
    )

    companies = load_gupy_companies(path)

    assert len(companies) == 2
    assert companies[0].category == "education_research"
    assert companies[0].priority is True
    assert companies[1].category == "logistics_mobility"
