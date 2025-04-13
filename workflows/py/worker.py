import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from apps.py.utils.debug import setup_debugger

from .activities.parliament import process_questions


class WorkerError(Exception):
    """Base exception for worker-related errors."""

    pass


async def create_worker(task_queue: str = "py-tasks-queue") -> Worker:
    """Create and configure a Temporal worker."""
    client = await Client.connect("localhost:7233")
    return Worker(client=client, task_queue=task_queue, activities=[process_questions])


async def main() -> None:
    """Entry point for the worker service."""
    # Optional: Enable debugging based on environment variable or command line argument
    setup_debugger()

    try:
        worker = await create_worker()
        logging.info(f"Worker listening on task queue: {worker.task_queue}")
        await worker.run()
    except Exception as e:
        logging.error(f"Worker failed: {e}")
        raise WorkerError(f"Worker execution failed: {e}") from e


if __name__ == "__main__":
    asyncio.run(main())
