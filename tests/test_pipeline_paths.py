from src.pipeline.paths import (
    compute_job_id,
    normalize_creator_handle,
    safe_upload_filename,
)


def test_normalize_creator_handle_strips_at_and_lowercases():
    assert normalize_creator_handle("@SomeCreator") == "somecreator"
    assert normalize_creator_handle("somecreator") == "somecreator"
    assert normalize_creator_handle("  @Some.Creator-1  ") == "some.creator-1"


def test_normalize_creator_handle_strips_unsafe_characters():
    # Slashes (and anything else outside the safe charset) are stripped.
    # Dots/hyphens survive because YouTube handles legitimately allow them;
    # the normalized handle is only ever hashed via compute_job_id, never
    # used directly as a filesystem path component, so this is safe.
    normalized = normalize_creator_handle("some/../creator")
    assert "/" not in normalized
    assert normalized == "some..creator"
    assert normalize_creator_handle("") == ""


def test_compute_job_id_is_deterministic():
    job_id_a = compute_job_id("abc123", "creator", "youtube")
    job_id_b = compute_job_id("abc123", "creator", "youtube")
    assert job_id_a == job_id_b


def test_compute_job_id_differs_by_platform_and_handle():
    base = compute_job_id("abc123", "creator", "youtube")
    different_platform = compute_job_id("abc123", "creator", "web")
    different_handle = compute_job_id("abc123", "other-creator", "youtube")
    different_video = compute_job_id("xyz999", "creator", "youtube")

    assert base != different_platform
    assert base != different_handle
    assert base != different_video


def test_compute_job_id_normalizes_handle_before_hashing():
    assert compute_job_id("abc123", "@Creator", "youtube") == compute_job_id(
        "abc123", "creator", "youtube"
    )


def test_safe_upload_filename_uses_allowed_extension():
    assert safe_upload_filename("job123", "clip.MP4") == "job123.mp4"
    assert safe_upload_filename("job123", "clip.mov") == "job123.mov"


def test_safe_upload_filename_falls_back_for_unknown_extension():
    assert safe_upload_filename("job123", "clip.exe") == "job123.mp4"


def test_safe_upload_filename_ignores_path_traversal_in_original_name():
    result = safe_upload_filename("job123", "../../etc/passwd.mp4")
    assert result == "job123.mp4"
    assert "/" not in result
    assert ".." not in result


def test_build_job_paths_creates_directories(tmp_path, monkeypatch):
    import src.pipeline.paths as paths_module

    monkeypatch.setattr(paths_module, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(paths_module, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(paths_module, "CACHE_ROOT", tmp_path / "outputs" / "_cache")

    result = paths_module.build_job_paths(job_id="job1", video_hash="hash1")

    assert result["output_dir"].is_dir()
    assert result["frames"].is_dir()
    assert result["audio"].parent.is_dir()
    assert result["transcription"].parent.is_dir()
    assert result["w_trends"].parent.is_dir()
    assert result["yt_syntax"].parent.is_dir()
