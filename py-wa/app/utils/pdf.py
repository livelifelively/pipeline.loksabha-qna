import asyncio
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import aiohttp
from pydantic import BaseModel, Field


class DownloadConfig(BaseModel):
    """Configuration for PDF download."""

    output_directory: Path = Field(..., description="Directory to save downloaded files")
    filename_generator: Callable[[str, int], str] = Field(..., description="Function to generate filenames")
    timeout_ms: int = Field(default=30000, description="Timeout in milliseconds")
    retries: int = Field(default=5, description="Number of retry attempts")
    retry_delay_ms: int = Field(default=2000, description="Delay between retries in milliseconds")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing files")

    class Config:
        arbitrary_types_allowed = True  # To allow Path and Callable types


async def download_pdfs(urls: List[str], config: DownloadConfig) -> List[Tuple[str, bool]]:
    """
    Download PDFs from given URLs.

    Args:
        urls: List of URLs to download from
        config: Download configuration

    Returns:
        List[Tuple[str, bool]]: List of tuples containing (file_path, was_downloaded)
    """

    async def download_single(url: str, index: int) -> Optional[Tuple[str, bool]]:
        filename = config.filename_generator(url, index)
        output_path = config.output_directory / filename

        if output_path.exists() and not config.overwrite_existing:
            return str(output_path), False

        for attempt in range(config.retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=config.timeout_ms / 1000) as response:
                        if response.status == 200:
                            output_path.write_bytes(await response.read())
                            return str(output_path), True
            except Exception:
                if attempt == config.retries - 1:
                    raise
                await asyncio.sleep(config.retry_delay_ms / 1000)
        return None

    tasks = [download_single(url, i) for i, url in enumerate(urls)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None values and raise any exceptions
    downloaded_results = []
    for result in results:
        if isinstance(result, Exception):
            raise result
        if result:
            downloaded_results.append(result)

    return downloaded_results
