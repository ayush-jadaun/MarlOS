"""Unit tests for result aggregation."""

import pytest
from agent.pipeline.aggregator import JobGroup, GroupStatus


class TestJobGroup:
    def test_group_creation(self):
        group = JobGroup()
        assert group.group_id is not None
        assert group.job_ids == []
        assert group.results == {}

    def test_status_pending(self):
        group = JobGroup()
        assert group.status == GroupStatus.PENDING

    def test_status_running(self):
        group = JobGroup(job_ids=["job-1", "job-2"])
        assert group.status == GroupStatus.RUNNING

    def test_status_partial(self):
        group = JobGroup(job_ids=["job-1", "job-2"])
        group.results["job-1"] = {"status": "success", "result": {"output": "ok"}}
        assert group.status == GroupStatus.PARTIAL

    def test_status_completed(self):
        group = JobGroup(job_ids=["job-1", "job-2"])
        group.results["job-1"] = {"status": "success", "result": {}}
        group.results["job-2"] = {"status": "success", "result": {}}
        assert group.status == GroupStatus.COMPLETED

    def test_status_all_failed(self):
        group = JobGroup(job_ids=["job-1"])
        group.results["job-1"] = {"status": "failed", "result": None}
        assert group.status == GroupStatus.FAILED

    def test_progress(self):
        group = JobGroup(job_ids=["job-1", "job-2", "job-3", "job-4"])
        assert group.progress == 0.0
        group.results["job-1"] = {"status": "success"}
        assert group.progress == 0.25
        group.results["job-2"] = {"status": "success"}
        assert group.progress == 0.5

    def test_to_dict(self):
        group = JobGroup(group_id="test-group", job_ids=["j1", "j2"])
        group.results["j1"] = {"status": "success", "result": {"x": 1}}
        d = group.to_dict()
        assert d["group_id"] == "test-group"
        assert d["total_jobs"] == 2
        assert d["completed_jobs"] == 1
        assert d["progress"] == 0.5
        assert d["status"] == "partial"
        assert "j1" in d["results"]
