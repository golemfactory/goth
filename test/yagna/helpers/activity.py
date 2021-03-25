"""Activity helpers."""

import os
from pathlib import Path

from goth.runner import Runner


def vm_exe_script(runner: Runner, output_file: str = "output.png"):
    """VM exe script builder."""
    """Create a VM exe script for running a Blender task."""

    output_path = Path(runner.web_root_path) / output_file
    if output_path.exists():
        os.remove(output_path)

    web_server_addr = f"http://{runner.host_address}:{runner.web_server_port}"

    return [
        {"deploy": {}},
        {"start": {}},
        {
            "transfer": {
                "from": f"{web_server_addr}/scene.blend",
                "to": "container:/golem/resource/scene.blend",
            }
        },
        {
            "transfer": {
                "from": f"{web_server_addr}/params.json",
                "to": "container:/golem/work/params.json",
            }
        },
        {"run": {"entry_point": "/golem/entrypoints/run-blender.sh", "args": []}},
        {
            "transfer": {
                "from": f"container:/golem/output/{output_file}",
                "to": f"{web_server_addr}/upload/{output_file}",
            }
        },
    ]


def wasi_exe_script(runner: Runner, output_file: str = "upload_file"):
    """WASI exe script builder."""
    """Create a WASI exe script for running a WASI tutorial task."""

    output_path = Path(runner.web_root_path) / output_file
    if output_path.exists():
        os.remove(output_path)

    web_server_addr = f"http://{runner.host_address}:{runner.web_server_port}"

    return [
        {"deploy": {}},
        {"start": {"args": []}},
        {
            "transfer": {
                "from": f"{web_server_addr}/params.json",
                "to": "container:/input/file_in",
            }
        },
        {
            "run": {
                "entry_point": "rust-wasi-tutorial",
                "args": ["/input/file_in", "/output/file_cp"],
            }
        },
        {
            "transfer": {
                "from": "container:/output/file_cp",
                "to": f"{web_server_addr}/upload/{output_file}",
            }
        },
    ]
