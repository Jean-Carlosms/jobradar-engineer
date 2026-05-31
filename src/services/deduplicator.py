from __future__ import annotations

from src.models.job import JobListing
from src.utils.text_cleaner import compact_key


def deduplicate_jobs(jobs: list[JobListing]) -> list[JobListing]:
    by_url: dict[str, JobListing] = {}
    without_url: list[JobListing] = []

    for job in jobs:
        url_key = (job.url or "").strip().lower()
        if not url_key:
            without_url.append(job)
            continue

        existing = by_url.get(url_key)
        if existing is None or job.match_score > existing.match_score:
            by_url[url_key] = job

    by_identity: dict[str, JobListing] = {}

    for job in list(by_url.values()) + without_url:
        identity_key = compact_key(job.title, job.company, job.location)
        existing = by_identity.get(identity_key)
        if existing is None or job.match_score > existing.match_score:
            by_identity[identity_key] = job

    return sorted(by_identity.values(), key=lambda item: item.match_score, reverse=True)
