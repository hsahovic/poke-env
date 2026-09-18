import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(
    sys.platform == "win32", reason="The CI startup script requires bash"
)
@pytest.mark.parametrize(
    "npm_exit,node_command,curl_exit,expected_exit,expected_output",
    [
        (23, "exit 0", 0, 23, ""),
        (0, "echo startup-crash; exit 42", 7, 42, "startup-crash"),
        (0, "exit 0", 7, 1, "exited before becoming ready"),
        (0, "exec sleep 30", 7, 1, "did not become ready"),
        (0, "exec sleep 30", 0, 0, ""),
    ],
)
def test_showdown_startup(
    tmp_path, npm_exit, node_command, curl_exit, expected_exit, expected_output
):
    showdown = tmp_path / "pokemon-showdown"
    config = showdown / "config"
    config.mkdir(parents=True)
    (config / "config-example.js").write_text("exports.backdoor = true;\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, command in {
        "npm": f"exit {npm_exit}",
        "node": node_command,
        "curl": f"exit {curl_exit}",
    }.items():
        executable = bin_dir / name
        executable.write_text(f"#!/usr/bin/env bash\n{command}\n")
        executable.chmod(0o755)

    script = Path(__file__).resolve().parents[1] / "scripts/ci_setup_showdown.sh"
    process = subprocess.Popen(
        ["bash", str(script)],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "SHOWDOWN_STARTUP_TIMEOUT": "2",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=8)
        assert process.returncode == expected_exit, output
        assert expected_output in output
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        process.wait()
