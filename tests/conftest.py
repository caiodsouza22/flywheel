"""Shared fixtures for flywheel tests."""

from __future__ import annotations

import pytest

from flywheel.models import Job, JobState


@pytest.fixture
def sample_job() -> Job:
    return Job(job_id="job_sample", queue="default", payload={"x": 1}, state=JobState.PENDING)
