from src.models.job import JobListing
from src.services.deduplicator import deduplicate_jobs


def test_deduplicates_by_url_and_keeps_highest_score():
    low = JobListing("Engenheiro", "ACME", "Sorocaba", "A", "https://example.com/job", match_score=5)
    high = JobListing("Engenheiro", "ACME", "Sorocaba", "B", "https://example.com/job", match_score=20)

    result = deduplicate_jobs([low, high])

    assert len(result) == 1
    assert result[0].source == "B"


def test_deduplicates_by_title_company_location():
    first = JobListing("Automation Engineer", "ACME", "Campinas", "A", "https://example.com/a", match_score=10)
    duplicate = JobListing("automation engineer", "Acme", "Campinas", "B", "https://example.com/b", match_score=8)

    result = deduplicate_jobs([first, duplicate])

    assert len(result) == 1
    assert result[0].url == "https://example.com/a"
