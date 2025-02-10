import asyncio
from temporalio import worker, client
from activities import pyActivity  # Import the activity


async def main():
    task_queue = "ts-tasks-queue"
    
    # First create client
    client_obj = await client.Client.connect("localhost:7233")
    
    # Create worker using the new API
    worker_instance = worker.Worker(
        client=client_obj,
        task_queue=task_queue,
        activities=[pyActivity],
        workflows=[]
    )

    print(f"Python worker listening on task queue: {task_queue}")
    await worker_instance.run()

if __name__ == "__main__":
    asyncio.run(main())