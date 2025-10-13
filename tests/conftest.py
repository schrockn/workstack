"""Pytest configuration and shared fixtures."""

import asyncio
import gc

import pytest


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case.

    This fixture ensures proper cleanup of event loops between tests,
    preventing "Event loop is closed" errors when running async tests
    alongside tests that use subprocess (which can create async transports).
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Ensure all pending tasks are completed
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    # Shutdown async generators
    loop.run_until_complete(loop.shutdown_asyncgens())

    # Give subprocess transports time to close
    loop.run_until_complete(asyncio.sleep(0))

    # Force garbage collection to cleanup any remaining subprocess transports
    gc.collect()

    loop.close()
