#!/usr/bin/env python3
"""A wrapper script for starting the test harness in interactive mode."""

import pytest

from goth.project import TEST_DIR


if __name__ == "__main__":
    test_file = TEST_DIR / "yagna" / "interactive" / "test_interactive_vm.py"
    pytest.main([str(test_file), "-svx"])
