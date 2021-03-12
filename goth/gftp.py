"""A module that provides a wrapper for `gftp` binary running in a docker container.

Note: `DEBUG_GFTP` is an environment variable used by `yapapi` to enable debug logs
from its gftp module. We use the same variable here to set logging level to `DEBUG`
in this wrapper script.

For testing you can use an example request:

  {"jsonrpc": "2.0", "method": "version", "params": {}, "id":1}

The response should be something like:

  {"jsonrpc":"2.0","id":1,"result":"0.6.1 (a282c32 2021-03-08 build #125)"}
"""

import json
import logging
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import threading
from typing import List, Tuple

import docker
from docker.utils.socket import frames_iter


logging.basicConfig(
    # This is the format used by default in yapapi's examples:
    format="[%(asctime)s %(levelname)s %(name)s] %(message)s",
    level=(logging.DEBUG if os.environ.get("DEBUG_GFTP") else logging.INFO),
)

logger = logging.getLogger("goth.gftp")


# Fixed path at which the volume used to exchange files between this script and
# the `gftp` binary running in the container is mounted in the container
CONTAINER_MOUNT_POINT = "/gftp_volume"


def create_gftp_dirs(requestor_container: str) -> Tuple[Path, Path]:
    """Create a directory with `gftp` script, and a working directory for the script.

    Returns a pair `(script_dir, volume_dir)` where
    - `script_dir` is the directory in which the `gftp` wrapper script is created;
    - `volume_dir` is the directory that should be mounted in the docker container
      running the `gftp` binary at `CONTAINER_MOUNT_POINT`; the wrapper script
      will be set up to read files from, and store them in this directory.
    """
    volume_dir = Path(tempfile.mkdtemp())
    (volume_dir / "in").mkdir()
    (volume_dir / "out").mkdir()

    script_dir = tempfile.mkdtemp()
    script_path = Path(script_dir) / "gftp"
    with open(script_path, "w") as script_file:
        script_file.writelines(
            [
                "#!/bin/sh\n",
                f"python -m goth.gftp {requestor_container} {volume_dir} $*\n",
            ]
        )
    stats = os.stat(script_path)
    os.chmod(script_path, stats.st_mode | stat.S_IEXEC)

    return Path(script_dir), Path(volume_dir)


def _mangle_path(path: Path) -> str:
    """Mangle `path` to a string that can be used as a filename.

    The mangling is deterministic and injective.
    """
    return str(path).replace("SLASH", "SSLASHH").replace(os.sep, "_SLASH_")


def run_gftp_server(gftp_container: str, gftp_volume: Path):
    """Run the `gftp server` command in `gftp_container` and communicate with it.

    Forwards requests read from stdin to the remote command and prints responses
    from the remote command to stdout.

    Makes copies of published files in the `gftp_volume` dir so that they can be
    accessed by the remote command (and modifies requests to reflect modified
    file locations).

    The protocol for communicating with remote command over a socket is described
    here: https://docs.docker.com/engine/api/v1.24/#attach-to-a-container, but
    the link is provided only for reference, we use higher-level utility functions
    from Python Docker SDK here.
    """

    # Start the command and create a socket
    api_client = docker.APIClient()
    exec_id = api_client.exec_create(
        gftp_container, "gftp server", stdin=True, tty=False
    )
    socket = api_client.exec_start(exec_id["Id"], socket=True)._sock

    def container_path_to_volume_path(container_path: Path) -> Path:
        container_path = container_path.resolve()
        relative_path = container_path.relative_to(Path(CONTAINER_MOUNT_POINT))
        return gftp_volume / relative_path

    def volume_path_to_container_path(volume_path: Path) -> Path:
        volume_path = volume_path.resolve()
        relative_path = volume_path.relative_to(gftp_volume)
        return Path(CONTAINER_MOUNT_POINT) / relative_path

    def copy_files_to_volume(files: List[str]) -> List[str]:
        """Copy `files` to the shared volume, return a list of their container paths."""

        container_files = []
        for file in files:
            orig_path = Path(file).resolve()
            copy_path = gftp_volume / "in" / _mangle_path(orig_path)
            shutil.copy(str(orig_path), str(copy_path))
            container_path = volume_path_to_container_path(copy_path)
            container_files.append(str(container_path))
        return container_files

    def response_reader():
        """Read remote command responses from the socket."""

        for stream_type, data in frames_iter(socket, tty=False):
            response = data.decode("utf-8")
            if stream_type == 1:
                # stream_type == 1 means it's from the command's stdout
                logger.debug("received: %s", response.encode("utf-8"))
                try:
                    msg = json.loads(response)
                    if "result" in msg and "file" in msg["result"]:
                        container_file = Path(msg["result"]["file"])
                        volume_file = container_path_to_volume_path(container_file)
                        msg["result"]["file"] = str(volume_file)
                        response = json.dumps(msg) + "\n"
                except Exception as e:
                    logger.warning(
                        "Cannot parse gftp response '%s': %s",
                        response.encode("utf-8"),
                        e,
                    )
                    # Return the response as is
                sys.stdout.write(response)
                sys.stdout.flush()
            elif stream_type == 2:
                # it's from the command's stderr
                logger.debug("stderr: %s", response.strip())
            else:
                raise ValueError(
                    f"Unexpected stream type in a frame header: {stream_type}"
                )

    # Reading responses needs to be done in a separate thread, otherwise it'll block
    reader_thread = threading.Thread(target=response_reader, daemon=True)
    reader_thread.start()

    # Read requests from stdin and write them to the socket
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            method = msg["method"]
            params = msg["params"]
            if method == "publish":
                files = params["files"]
                container_files = copy_files_to_volume(files)
                logger.debug(
                    "replaced `files`; original: %s, new: %s", files, container_files
                )
                params["files"] = container_files
                line = json.dumps(msg) + "\n"
            elif method == "receive":
                output_file = Path(params["output_file"])
                container_file = (
                    Path(CONTAINER_MOUNT_POINT) / "out" / _mangle_path(output_file)
                )
                logger.debug(
                    "replaced `output_file`; original: %s, new: %s",
                    output_file,
                    container_file,
                )
                params["output_file"] = str(container_file)
                line = json.dumps(msg) + "\n"
        except Exception:
            # Pass the request as is
            pass

        logger.debug("sending: (%s)", line.encode("utf-8"))
        socket.sendall(line.encode("utf-8"))

    socket.close()


if __name__ == "__main__":

    container_name = sys.argv[1]
    volume_dir = sys.argv[2]
    command = sys.argv[3]

    if command == "server":
        run_gftp_server(container_name, Path(volume_dir))
    else:
        raise ValueError(f"Command not supported: {command}")
