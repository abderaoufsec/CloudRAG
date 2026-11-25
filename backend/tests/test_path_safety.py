from types import SimpleNamespace
from unittest.mock import Mock

from app.api import documents as documents_api


def _patch_dirs(monkeypatch, tmp_path):
    documents_dir = tmp_path / "documents"
    processed_dir = tmp_path / "processed"
    documents_dir.mkdir()
    processed_dir.mkdir()

    monkeypatch.setattr(documents_api, "DOCUMENTS_DIR", documents_dir)
    monkeypatch.setattr(documents_api, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(
        documents_api.rag_pipeline,
        "delete_document",
        Mock(),
    )

    return documents_dir, processed_dir


def test_cleanup_ignores_paths_outside_data_dir(tmp_path, monkeypatch):
    _patch_dirs(monkeypatch, tmp_path)

    victim = tmp_path / "victim.txt"
    victim.write_text("keep me", encoding="utf-8")

    document = SimpleNamespace(
        document_id="../victim",
        file_type=".txt",
    )

    documents_api._delete_document_artifacts(Mock(), document)

    assert victim.exists()


def test_cleanup_removes_files_inside_data_dir(tmp_path, monkeypatch):
    documents_dir, processed_dir = _patch_dirs(monkeypatch, tmp_path)

    original_file = documents_dir / "abc.txt"
    processed_file = processed_dir / "abc.txt"
    original_file.write_text("original", encoding="utf-8")
    processed_file.write_text("processed", encoding="utf-8")

    document = SimpleNamespace(
        document_id="abc",
        file_type=".txt",
    )

    documents_api._delete_document_artifacts(Mock(), document)

    assert not original_file.exists()
    assert not processed_file.exists()
