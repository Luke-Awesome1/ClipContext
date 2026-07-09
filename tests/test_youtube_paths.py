from src.pipeline import paths as paths_module


def test_resolve_upload_video_path_finds_matching_job_video(tmp_path, monkeypatch):
    monkeypatch.setattr(paths_module, "UPLOADS_DIR", tmp_path)
    video_file = tmp_path / "abc123def456.mp4"
    video_file.write_bytes(b"fake video bytes")

    resolved = paths_module.resolve_upload_video_path("abc123def456")

    assert resolved == video_file


def test_resolve_upload_video_path_returns_none_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(paths_module, "UPLOADS_DIR", tmp_path)

    assert paths_module.resolve_upload_video_path("does-not-exist") is None


def test_resolve_upload_video_path_ignores_disallowed_extensions(tmp_path, monkeypatch):
    monkeypatch.setattr(paths_module, "UPLOADS_DIR", tmp_path)
    (tmp_path / "abc123.txt").write_bytes(b"not a video")

    assert paths_module.resolve_upload_video_path("abc123") is None


def test_resolve_upload_video_path_handles_missing_uploads_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(paths_module, "UPLOADS_DIR", tmp_path / "does-not-exist")

    assert paths_module.resolve_upload_video_path("abc123") is None
