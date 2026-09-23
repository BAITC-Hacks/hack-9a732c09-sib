"""Thread-safe, process-local run store with one evaluation worker."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from .runner import IncompleteRunError, StrategyRunner
from .schemas import Error, RunAccepted, RunFailed, RunPending, RunRequest, RunSnapshot

logger = logging.getLogger(__name__)


class RunService:
    def __init__(self, runner=None):
        self.runner = runner if runner is not None else StrategyRunner()
        self._runs: dict[UUID, RunSnapshot] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="strategy")

    def create(self, request: RunRequest) -> RunAccepted:
        accepted = RunAccepted(run_id=uuid4(), status="queued", created_at=datetime.now(timezone.utc),
                               source="mock_environment")
        with self._lock:
            self._runs[accepted.run_id] = RunPending(**accepted.model_dump())
            try:
                self._executor.submit(self._execute, accepted, request.seed)
            except Exception:
                del self._runs[accepted.run_id]
                raise
        return accepted

    def _execute(self, accepted, seed):
        with self._lock:
            self._runs[accepted.run_id] = RunPending(**dict(accepted.model_dump(), status="running"))
        try:
            result = self.runner.run(accepted, seed)
        except Exception as exc:
            # No exception text/stack trace in the API or evaluator-derived warnings.
            logger.error("Run %s failed (%s)", accepted.run_id, type(exc).__name__)
            code = "INCOMPLETE_RUN" if isinstance(exc, IncompleteRunError) else "RUN_FAILED"
            result = RunFailed(
                **dict(accepted.model_dump(), status="failed"), completed_at=datetime.now(timezone.utc),
                error=Error(code=code, message="Demo run could not be completed.", details=[]), warnings=[],
            )
        with self._lock:
            self._runs[accepted.run_id] = result

    def get(self, run_id: UUID):
        with self._lock:
            run = self._runs.get(run_id)
            return None if run is None else run.model_copy(deep=True)

    def close(self):
        self._executor.shutdown(wait=True)
