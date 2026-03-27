"""
Pipeline execution engine.
Manages the lifecycle of pipelines: validates DAG, submits ready steps,
monitors completion, passes results between steps.
"""

import asyncio
import time
import logging
from typing import Optional

from .dag import Pipeline, PipelineStep, PipelineStatus, StepStatus

logger = logging.getLogger(__name__)


class PipelineEngine:
    """
    Executes pipelines by submitting steps to the MarlOS network.
    Steps are independently auctioned. Output of step A is injected
    into the payload of dependent step B.
    """

    def __init__(self, agent):
        self.agent = agent
        self.pipelines: dict[str, Pipeline] = {}
        self._monitors: dict[str, asyncio.Task] = {}

    async def submit_pipeline(self, pipeline: Pipeline) -> Pipeline:
        """Validate and start executing a pipeline."""
        errors = pipeline.validate()
        if errors:
            pipeline.status = PipelineStatus.FAILED
            pipeline.error = "; ".join(errors)
            return pipeline

        pipeline.status = PipelineStatus.RUNNING
        self.pipelines[pipeline.id] = pipeline

        print(f"[PIPELINE] Starting pipeline '{pipeline.name or pipeline.id}' with {len(pipeline.steps)} steps")

        # Start monitoring loop
        task = asyncio.create_task(self._run_pipeline(pipeline))
        self._monitors[pipeline.id] = task

        return pipeline

    async def _run_pipeline(self, pipeline: Pipeline):
        """Main pipeline execution loop."""
        try:
            while not pipeline.is_complete():
                # Find steps that are ready to run
                ready = pipeline.get_ready_steps()

                for step in ready:
                    await self._submit_step(pipeline, step)

                # Check for submitted steps that have completed
                for step in pipeline.steps:
                    if step.status == StepStatus.SUBMITTED:
                        self._check_step_completion(step)

                # If nothing is ready and nothing is running, we're stuck
                active = [s for s in pipeline.steps if s.status in (StepStatus.SUBMITTED, StepStatus.PENDING)]
                ready_or_submitted = [s for s in active if s.status == StepStatus.SUBMITTED]
                if not ready and not ready_or_submitted:
                    # All remaining steps have unmet deps from failed steps
                    for step in pipeline.steps:
                        if step.status == StepStatus.PENDING:
                            step.status = StepStatus.SKIPPED
                    break

                await asyncio.sleep(0.5)

            # Pipeline done
            if pipeline.has_failed():
                pipeline.status = PipelineStatus.FAILED
                failed = [s for s in pipeline.steps if s.status == StepStatus.FAILED]
                pipeline.error = f"Steps failed: {[s.id for s in failed]}"
            else:
                pipeline.status = PipelineStatus.COMPLETED

            pipeline.completed_at = time.time()
            duration = pipeline.completed_at - pipeline.created_at
            print(f"[PIPELINE] Pipeline '{pipeline.id}' {pipeline.status.value} in {duration:.1f}s")

        except Exception as e:
            pipeline.status = PipelineStatus.FAILED
            pipeline.error = str(e)
            logger.error(f"Pipeline error: {e}")

    async def _submit_step(self, pipeline: Pipeline, step: PipelineStep):
        """Submit a pipeline step as a job to the network."""
        step.status = StepStatus.SUBMITTED
        step.started_at = time.time()

        # Inject results from dependencies into payload
        payload = dict(step.payload)
        for dep_id in step.depends_on:
            dep_step = pipeline.get_step(dep_id)
            if dep_step and dep_step.result:
                payload[f"_input_{dep_id}"] = dep_step.result

        print(f"[PIPELINE] Submitting step '{step.id}' ({step.job_type}) -> job {step.job_id}")

        try:
            from ..p2p.protocol import MessageType

            await self.agent.p2p.broadcast_message(
                MessageType.JOB_BROADCAST,
                job_id=step.job_id,
                job_type=step.job_type,
                priority=step.priority,
                payment=step.payment,
                deadline=time.time() + 300,
                payload=payload,
            )
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"Failed to submit step {step.id}: {e}")

    def _check_step_completion(self, step: PipelineStep):
        """Check if a submitted step's job has completed."""
        result = self.agent.job_results.get(step.job_id)
        if result is None:
            return

        step.completed_at = time.time()

        if hasattr(result, 'status'):
            status_val = result.status.value if hasattr(result.status, 'value') else str(result.status)
        else:
            status_val = str(result)

        if status_val in ("success", "JobStatus.SUCCESS"):
            step.status = StepStatus.COMPLETED
            step.result = result.result if hasattr(result, 'result') else {}
            print(f"[PIPELINE] Step '{step.id}' completed")
        else:
            step.status = StepStatus.FAILED
            step.error = result.error if hasattr(result, 'error') else "Job failed"
            print(f"[PIPELINE] Step '{step.id}' failed: {step.error}")

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        return self.pipelines.get(pipeline_id)

    def list_pipelines(self) -> list[dict]:
        return [p.to_dict() for p in self.pipelines.values()]
