import asyncio

from app.activities.parliament import process_questions


async def main():
    try:
        breakpoint()
        result = await process_questions("test")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
