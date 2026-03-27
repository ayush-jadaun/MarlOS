"""
Result aggregation for batch job submissions.
Submit N jobs with a group ID, query for combined results.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class GroupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class JobGroup:
    """A group of related jobs submitted together."""
    group_id: str = None
    job_ids: list[str] = field(default_factory=list)
    results: dict[str, dict] = field(default_factory=dict)  # job_id -> result
    created_at: float = field(default_factory=time.time)
    completed_at: float = None

    def __post_init__(self):
        if self.group_id is None:
            self.group_id = f"group-{str(uuid.uuid4())[:8]}"

    @property
    def status(self) -> GroupStatus:
        if not self.job_ids:
            return GroupStatus.PENDING
        completed = len(self.results)
        total = len(self.job_ids)
        if completed == 0:
            return GroupStatus.RUNNING
        elif completed == total:
            failed = sum(1 for r in self.results.values() if r.get("status") == "failed")
            return GroupStatus.FAILED if failed == total else GroupStatus.COMPLETED
        else:
            return GroupStatus.PARTIAL

    @property
    def progress(self) -> float:
        if not self.job_ids:
            return 0.0
        return len(self.results) / len(self.job_ids)

    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "status": self.status.value,
            "total_jobs": len(self.job_ids),
            "completed_jobs": len(self.results),
            "progress": self.progress,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "results": self.results,
        }


class ResultAggregator:
    """Manages groups of related jobs and aggregates their results."""

    def __init__(self, agent):
        self.agent = agent
        self.groups: dict[str, JobGroup] = {}

    async def submit_group(self, jobs: list[dict], group_id: str = None) -> JobGroup:
        """Submit a batch of jobs as a group."""
        group = JobGroup(group_id=group_id)

        from ..p2p.protocol import MessageType

        for job_spec in jobs:
            job_id = job_spec.get("job_id", f"grp-{group.group_id}-{str(uuid.uuid4())[:6]}")
            group.job_ids.append(job_id)

            await self.agent.p2p.broadcast_message(
                MessageType.JOB_BROADCAST,
                job_id=job_id,
                job_type=job_spec.get("job_type", "shell"),
                priority=job_spec.get("priority", 0.5),
                payment=job_spec.get("payment", 50.0),
                deadline=job_spec.get("deadline", time.time() + 300),
                payload=job_spec.get("payload", {}),
            )

        self.groups[group.group_id] = group

        # Start background monitor
        asyncio.create_task(self._monitor_group(group))

        print(f"[AGGREGATOR] Submitted group '{group.group_id}' with {len(group.job_ids)} jobs")
        return group

    async def _monitor_group(self, group: JobGroup):
        """Monitor job completion and collect results."""
        timeout = 300  # 5 minutes max
        start = time.time()

        while time.time() - start < timeout:
            for job_id in group.job_ids:
                if job_id in group.results:
                    continue  # Already collected

                result = self.agent.job_results.get(job_id)
                if result:
                    group.results[job_id] = {
                        "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
                        "result": result.result if hasattr(result, 'result') else None,
                        "duration": result.duration if hasattr(result, 'duration') else None,
                    }

            if len(group.results) == len(group.job_ids):
                group.completed_at = time.time()
                print(f"[AGGREGATOR] Group '{group.group_id}' completed: {len(group.results)}/{len(group.job_ids)} jobs")
                return

            await asyncio.sleep(0.5)

        print(f"[AGGREGATOR] Group '{group.group_id}' timed out: {len(group.results)}/{len(group.job_ids)} completed")

    def get_group(self, group_id: str) -> Optional[JobGroup]:
        return self.groups.get(group_id)

    def list_groups(self) -> list[dict]:
        return [g.to_dict() for g in self.groups.values()]
