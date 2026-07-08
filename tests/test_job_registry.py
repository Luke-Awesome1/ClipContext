import threading
import time

from src.api.jobs import JobRegistry
from src.api.schemas import JobStatus
from src.pipeline.schemas import PipelineStage


def test_get_or_create_returns_new_record_once():
    registry = JobRegistry()

    record_a, created_a = registry.get_or_create("job-1")
    record_b, created_b = registry.get_or_create("job-1")

    assert created_a is True
    assert created_b is False
    assert record_a is record_b
    assert record_a.status == JobStatus.QUEUED


def test_update_progress_transitions_to_processing():
    registry = JobRegistry()
    registry.get_or_create("job-1")

    registry.update_progress(
        "job-1",
        stage=PipelineStage.TRANSCRIBING,
        progress=32,
        message="Transcribing audio",
    )

    record = registry.get("job-1")
    assert record.status == JobStatus.PROCESSING
    assert record.stage == PipelineStage.TRANSCRIBING
    assert record.progress == 32
    assert record.message == "Transcribing audio"


def test_set_result_marks_completed():
    registry = JobRegistry()
    registry.get_or_create("job-1")

    registry.set_result("job-1", result="fake-result")

    record = registry.get("job-1")
    assert record.status == JobStatus.COMPLETED
    assert record.stage == PipelineStage.COMPLETED
    assert record.progress == 100
    assert record.result == "fake-result"
    assert record.error is None


def test_set_error_marks_failed_and_preserves_message():
    registry = JobRegistry()
    registry.get_or_create("job-1")

    registry.set_error("job-1", "video too short")

    record = registry.get("job-1")
    assert record.status == JobStatus.FAILED
    assert record.error == "video too short"


def test_updates_to_unknown_job_id_are_ignored():
    registry = JobRegistry()

    # Should not raise even though "missing" was never created.
    registry.update_progress(
        "missing", stage=PipelineStage.QUEUED, progress=0, message="noop"
    )
    registry.set_result("missing", result="x")
    registry.set_error("missing", "x")

    assert registry.get("missing") is None


def test_registry_is_thread_safe_under_concurrent_creation():
    registry = JobRegistry()
    results = []

    def worker():
        _record, created = registry.get_or_create("shared-job")
        results.append(created)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    # Exactly one thread should have created the record.
    assert results.count(True) == 1
    assert results.count(False) == 19
