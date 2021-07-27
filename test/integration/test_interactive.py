"""Integration tests for the goth interactive mode."""

import asyncio
from pathlib import Path
import pytest

from goth.configuration import load_yaml
from goth.interactive import start_network, env_file


@pytest.mark.asyncio
async def test_interactive(
    capsys: pytest.CaptureFixture, default_goth_config: Path, log_dir: Path
) -> None:
    """Test if goth interactive mode launches correctly."""
    goth_config = load_yaml(default_goth_config, [])
    interactive_task = asyncio.create_task(start_network(goth_config, log_dir))

    async def _scan_stdout():
        expected_msg = "Local goth network ready"
        while True:
            stdout, _stderr = capsys.readouterr()
            if expected_msg in stdout:
                break
            await asyncio.sleep(0.1)

    try:
        await asyncio.wait_for(_scan_stdout(), timeout=90)
        assert env_file.exists()
    except asyncio.TimeoutError:
        pytest.fail("Timeout while waiting for interactive mode to start")
    finally:
        interactive_task.cancel()
        await interactive_task
