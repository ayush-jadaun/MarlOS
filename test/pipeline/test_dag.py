"""Unit tests for Pipeline DAG."""

import pytest
from agent.pipeline.dag import Pipeline, PipelineStep, PipelineStatus, StepStatus


class TestPipelineStep:
    def test_step_creation(self):
        step = PipelineStep(id="scan", job_type="port_scan", payload={"target": "192.168.1.0/24"})
        assert step.id == "scan"
        assert step.job_type == "port_scan"
        assert step.status == StepStatus.PENDING
        assert step.job_id is not None

    def test_step_defaults(self):
        step = PipelineStep(id="test", job_type="shell")
        assert step.payment == 50.0
        assert step.priority == 0.5
        assert step.depends_on == []
        assert step.result is None


class TestPipeline:
    def test_pipeline_creation(self):
        p = Pipeline(name="test-pipeline", steps=[
            PipelineStep(id="a", job_type="shell", payload={"command": "echo hello"}),
            PipelineStep(id="b", job_type="shell", payload={"command": "echo bye"}, depends_on=["a"]),
        ])
        assert p.status == PipelineStatus.PENDING
        assert len(p.steps) == 2
        assert p.id is not None

    def test_validate_valid_pipeline(self):
        p = Pipeline(steps=[
            PipelineStep(id="a", job_type="shell"),
            PipelineStep(id="b", job_type="shell", depends_on=["a"]),
            PipelineStep(id="c", job_type="shell", depends_on=["a", "b"]),
        ])
        errors = p.validate()
        assert errors == []

    def test_validate_missing_dependency(self):
        p = Pipeline(steps=[
            PipelineStep(id="a", job_type="shell", depends_on=["nonexistent"]),
        ])
        errors = p.validate()
        assert any("nonexistent" in e for e in errors)

    def test_validate_cycle_detection(self):
        p = Pipeline(steps=[
            PipelineStep(id="a", job_type="shell", depends_on=["b"]),
            PipelineStep(id="b", job_type="shell", depends_on=["a"]),
        ])
        errors = p.validate()
        assert any("cycle" in e.lower() for e in errors)

    def test_validate_self_cycle(self):
        p = Pipeline(steps=[
            PipelineStep(id="a", job_type="shell", depends_on=["a"]),
        ])
        errors = p.validate()
        assert any("cycle" in e.lower() for e in errors)

    def test_get_ready_steps_no_deps(self):
        p = Pipeline(steps=[
            PipelineStep(id="a", job_type="shell"),
            PipelineStep(id="b", job_type="shell"),
        ])
        ready = p.get_ready_steps()
        assert len(ready) == 2

    def test_get_ready_steps_with_deps(self):
        step_a = PipelineStep(id="a", job_type="shell")
        step_b = PipelineStep(id="b", job_type="shell", depends_on=["a"])
        p = Pipeline(steps=[step_a, step_b])

        # Initially only A is ready
        ready = p.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "a"

        # After A completes, B becomes ready
        step_a.status = StepStatus.COMPLETED
        ready = p.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "b"

    def test_get_ready_steps_multiple_deps(self):
        step_a = PipelineStep(id="a", job_type="shell")
        step_b = PipelineStep(id="b", job_type="shell")
        step_c = PipelineStep(id="c", job_type="shell", depends_on=["a", "b"])
        p = Pipeline(steps=[step_a, step_b, step_c])

        # Only A and B ready initially
        assert len(p.get_ready_steps()) == 2

        # After A completes, C still not ready (needs B)
        step_a.status = StepStatus.COMPLETED
        ready = p.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "b"

        # After B completes, C is ready
        step_b.status = StepStatus.COMPLETED
        ready = p.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "c"

    def test_is_complete(self):
        step_a = PipelineStep(id="a", job_type="shell")
        step_b = PipelineStep(id="b", job_type="shell")
        p = Pipeline(steps=[step_a, step_b])

        assert not p.is_complete()
        step_a.status = StepStatus.COMPLETED
        assert not p.is_complete()
        step_b.status = StepStatus.COMPLETED
        assert p.is_complete()

    def test_has_failed(self):
        step_a = PipelineStep(id="a", job_type="shell")
        p = Pipeline(steps=[step_a])

        assert not p.has_failed()
        step_a.status = StepStatus.FAILED
        assert p.has_failed()

    def test_from_dict(self):
        data = {
            "name": "security-scan",
            "steps": [
                {"id": "scan", "job_type": "port_scan", "payload": {"target": "10.0.0.0/24"}},
                {"id": "analyze", "job_type": "shell", "payload": {"command": "python analyze.py"}, "depends_on": ["scan"]},
            ],
        }
        p = Pipeline.from_dict(data)
        assert p.name == "security-scan"
        assert len(p.steps) == 2
        assert p.steps[1].depends_on == ["scan"]

    def test_to_dict(self):
        p = Pipeline(name="test", steps=[
            PipelineStep(id="a", job_type="shell"),
        ])
        d = p.to_dict()
        assert d["name"] == "test"
        assert len(d["steps"]) == 1
        assert d["steps"][0]["id"] == "a"
        assert d["status"] == "pending"

    def test_parallel_steps(self):
        """Steps without dependencies can run in parallel."""
        p = Pipeline(steps=[
            PipelineStep(id="a", job_type="shell"),
            PipelineStep(id="b", job_type="shell"),
            PipelineStep(id="c", job_type="shell"),
            PipelineStep(id="final", job_type="shell", depends_on=["a", "b", "c"]),
        ])
        ready = p.get_ready_steps()
        assert len(ready) == 3  # a, b, c all ready
        assert all(s.id != "final" for s in ready)

    def test_diamond_dag(self):
        """A -> B, A -> C, B -> D, C -> D (diamond shape)."""
        step_a = PipelineStep(id="a", job_type="shell")
        step_b = PipelineStep(id="b", job_type="shell", depends_on=["a"])
        step_c = PipelineStep(id="c", job_type="shell", depends_on=["a"])
        step_d = PipelineStep(id="d", job_type="shell", depends_on=["b", "c"])
        p = Pipeline(steps=[step_a, step_b, step_c, step_d])

        assert p.validate() == []
        assert len(p.get_ready_steps()) == 1  # only a

        step_a.status = StepStatus.COMPLETED
        assert len(p.get_ready_steps()) == 2  # b and c

        step_b.status = StepStatus.COMPLETED
        assert len(p.get_ready_steps()) == 1  # only c

        step_c.status = StepStatus.COMPLETED
        assert len(p.get_ready_steps()) == 1  # d
