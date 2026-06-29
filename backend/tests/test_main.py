from frogswork_api.main import app


def test_app_title():
    assert app.title == "FrogsWork File Storage API"
