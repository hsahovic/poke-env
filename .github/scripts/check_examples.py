import glob
import os
import sys
import subprocess


def start_group(group_name: str):
    print(f"::group::{group_name}", flush=True)


def end_group():
    print("::endgroup::", flush=True)


def check_file(file_abs_path: str) -> bool:
    print(f"Running command {sys.executable} {file_abs_path}", flush=True)
    try:
        process = subprocess.run([sys.executable, file_abs_path], shell=False)
    except subprocess.TimeoutExpired:
        return False
    print(f"Process completed with exit code {process.returncode}", flush=True)
    return process.returncode == 0


def main() -> bool:
    success = True
    examples_directory = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "examples",
    )
    for filename in glob.iglob(
        os.path.join(examples_directory, "**/*.py"), recursive=True
    ):
        start_group(f"Testing file {filename.replace(examples_directory, 'examples')}")
        if not check_file(filename):
            success = False
        end_group()
    return success


if __name__ == "__main__":
    print("Testing example files...", flush=True)
    if main():
        print("All example files ran successfully", flush=True)
        sys.exit(0)
    else:
        print("Not all example files ran successfully", flush=True)
        sys.exit(1)
