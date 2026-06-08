from app.services.resume_parser import build_profile_from_text


def test_build_profile_from_text_extracts_candidate_basics() -> None:
    text = """
    Amisha Negi
    SDE-2 with 4+ years of experience
    Skills: Python, Django, AngularJS, Elasticsearch, Redis, MySQL, Celery, AWS
    Education
    B.Tech Computer Science, Example University
    Projects
    Built distributed job-search APIs with Django and Redis.
    """

    profile = build_profile_from_text(text)

    assert profile["name"] == "Amisha Negi"
    assert profile["experience_years"] == 4
    assert "Python" in profile["skills"]
    assert "Django" in profile["skills"]
    assert "AWS" in profile["skills"]
    assert profile["education"]

