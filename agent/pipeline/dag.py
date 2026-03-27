"""
Pipeline DAG definitions for MarlOS job chaining.
A pipeline is a directed acyclic graph of jobs with dependencies.
"""

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    PENDING = "pending"
    WAITING = "waiting"       # Waiting for dependencies
    SUBMITTED = "submitted"   # Submitted to network (auctioning/executing)
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """A single step in a pipeline."""
    id: str
    job_type: str
    payload: dict = field(default_factory=dict)
    payment: float = 50.0
    priority: float = 0.5
    depends_on: list[str] = field(default_factory=list)

    # Runtime state
    status: StepStatus = StepStatus.PENDING
    job_id: str = None          # Assigned when submitted to network
    result: dict = None         # Result from execution
    error: str = None
    started_at: float = None
    completed_at: float = None

    def __post_init__(self):
        if self.job_id is None:
            self.job_id = f"pipe-{self.id}-{str(uuid.uuid4())[:6]}"


@dataclass
class Pipeline:
    """A pipeline of jobs with dependencies (DAG)."""
    id: str = None
    name: str = ""
    steps: list[PipelineStep] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: float = None
    error: str = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"pipeline-{str(uuid.uuid4())[:8]}"

    def validate(self) -> list[str]:
        """Validate the pipeline DAG. Returns list of errors (empty = valid)."""
        errors = []
        step_ids = {s.id for s in self.steps}

        # Check for duplicate IDs
        if len(step_ids) != len(self.steps):
            errors.append("Duplicate step IDs found")

        # Check dependencies exist
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step '{step.id}' depends on unknown step '{dep}'")

        # Check for cycles (topological sort)
        visited = set()
        in_progress = set()

        def has_cycle(step_id):
            if step_id in in_progress:
                return True
            if step_id in visited:
                return False
            in_progress.add(step_id)
            step = self.get_step(step_id)
            if step:
                for dep in step.depends_on:
                    if has_cycle(dep):
                        return True
            in_progress.remove(step_id)
            visited.add(step_id)
            return False

        for step in self.steps:
            if has_cycle(step.id):
                errors.append("Pipeline contains a cycle")
                break

        return errors

    def get_step(self, step_id: str) -> Optional[PipelineStep]:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_ready_steps(self) -> list[PipelineStep]:
        """Get steps whose dependencies are all completed."""
        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            deps_met = all(
                self.get_step(dep).status == StepStatus.COMPLETED
                for dep in step.depends_on
            )
            if deps_met:
                ready.append(step)
        return ready

    def is_complete(self) -> bool:
        return all(
            s.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED)
            for s in self.steps
        )

    def has_failed(self) -> bool:
        return any(s.status == StepStatus.FAILED for s in self.steps)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "steps": [
                {
                    "id": s.id,
                    "job_type": s.job_type,
                    "payload": s.payload,
                    "depends_on": s.depends_on,
                    "status": s.status.value,
                    "job_id": s.job_id,
                    "result": s.result,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pipeline":
        """Create pipeline from dict/YAML structure."""
        steps = []
        for step_data in data.get("steps", data.get("pipeline", [])):
            steps.append(PipelineStep(
                id=step_data["id"],
                job_type=step_data.get("job_type", step_data.get("type", "shell")),
                payload=step_data.get("payload", {}),
                payment=step_data.get("payment", 50.0),
                priority=step_data.get("priority", 0.5),
                depends_on=step_data.get("depends_on", []),
            ))

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            steps=steps,
        )
