from src.config import Settings
from src.models.job import Job, JobAnalysis
from src.services.email_sender import EmailSender


class DummySMTP:
    instances = []

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.started_tls = False
        self.logged_in = False
        self.sent = False
        DummySMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message):
        self.sent = True


def make_job(title: str, score: float, already_sent: bool = False) -> Job:
    return Job(
        id=1,
        title=title,
        company="Siemens",
        location="Campinas",
        source="Teste",
        url=f"https://example.com/{title.replace(' ', '-').lower()}",
        description_snippet="CLP Siemens",
        match_score=score,
        match_reason="Alta aderencia por conter Python, CLP e automacao.",
        priority_company=True,
        query_used='site:gupy.io/jobs "Engenheiro de Automacao" "Campinas"',
        already_sent=already_sent,
    )


def test_email_sender_filters_by_min_score_and_orders(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", email_dry_run=True)
    sender = EmailSender(settings)
    jobs = [make_job("Baixa", 20), make_job("Alta", 80), make_job("Media", 55)]

    selected = sender.select_jobs(jobs, min_score=50, limit=2)

    assert [job.title for job in selected] == ["Alta", "Media"]


def test_email_sender_dry_run_builds_organized_body(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", email_dry_run=True, email_to="dest@example.com")
    job = make_job("Engenheiro de Automacao", 82)

    sender = EmailSender(settings)
    assert sender.send_jobs([job], min_score=50, limit=10) is True

    message = sender.build_message([job], min_score=50, limit=10)
    body = message.get_content()
    assert message["To"] == "dest@example.com"
    assert "Engenheiro de Automacao" in body
    assert "Motivo: Alta aderencia" in body
    assert "Empresa prioritaria: sim" in body


def test_email_sender_includes_analysis_when_available(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", email_dry_run=True)
    job = make_job("Automation Engineer", 90)
    job.analysis = JobAnalysis(
        job_id=1,
        fit_level="alto",
        fit_score=86,
        analysis_summary="Aderencia alto por conter Python e CLP.",
        recruiter_message="Ola! Tenho interesse na vaga.",
    )

    body = EmailSender(settings).build_message([job], min_score=50, limit=10).get_content()

    assert "Fit level: alto" in body
    assert "Fit score: 86/100" in body
    assert "Aderencia alto" in body
    assert "Mensagem sugerida" in body


def test_email_sender_uses_starttls_for_tls_mode(monkeypatch, tmp_path):
    DummySMTP.instances = []
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)
    settings = Settings(
        database_path=tmp_path / "jobs.db",
        email_dry_run=False,
        smtp_use_tls=True,
        smtp_use_ssl=False,
        smtp_username="user",
        smtp_password="pass",
    )

    assert EmailSender(settings).send_jobs([make_job("Alta", 90)], min_score=50, limit=10) is True

    smtp = DummySMTP.instances[0]
    assert smtp.started_tls is True
    assert smtp.logged_in == ("user", "pass")
    assert smtp.sent is True


def test_email_sender_uses_ssl_without_starttls(monkeypatch, tmp_path):
    DummySMTP.instances = []
    monkeypatch.setattr("smtplib.SMTP_SSL", DummySMTP)
    settings = Settings(
        database_path=tmp_path / "jobs.db",
        email_dry_run=False,
        smtp_use_tls=False,
        smtp_use_ssl=True,
        smtp_username="user",
        smtp_password="pass",
    )

    assert EmailSender(settings).send_jobs([make_job("Alta", 90)], min_score=50, limit=10) is True

    smtp = DummySMTP.instances[0]
    assert smtp.started_tls is False
    assert smtp.sent is True


def test_email_sender_requires_credentials_for_real_send(monkeypatch, tmp_path):
    DummySMTP.instances = []
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)
    settings = Settings(
        database_path=tmp_path / "jobs.db",
        email_dry_run=False,
        smtp_username="",
        smtp_password="",
    )

    assert EmailSender(settings).send_jobs([make_job("Alta", 90)], min_score=50, limit=10) is False
    assert DummySMTP.instances == []
