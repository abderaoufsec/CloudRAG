import app.config as config
from app.config import Settings


def test_data_dir_defaults_to_project_data():
    settings = Settings(data_dir="")

    assert settings.resolved_data_dir == config.PROJECT_ROOT / "data"


def test_data_dir_override_is_resolved(tmp_path):
    settings = Settings(data_dir=str(tmp_path))

    assert settings.resolved_data_dir == tmp_path.resolve()
