#!/usr/bin/env python3
"""Test script to check ikuai-cli connectivity."""
import asyncio
import json
import os
import sys

async def test_cli():
    """Test the ikuai-cli connection."""
    binary_path = "/usr/local/bin/ikuai-cli"
    base_url = os.environ.get("IKUAI_CLI_BASE_URL", "http://192.168.1.1")
    token = os.environ.get("IKUAI_CLI_TOKEN", "")

    print(f"Testing ikuai-cli at: {binary_path}")
    print(f"Base URL: {base_url}")
    print(f"Token: {'***' if token else 'Not set'}")

    # Check if binary exists
    if not os.path.exists(binary_path):
        print(f"ERROR: Binary not found at {binary_path}")
        return False

    if not os.access(binary_path, os.X_OK):
        print(f"ERROR: Binary is not executable: {binary_path}")
        return False

    # Test system monitor command
    print("\nTesting 'monitor system --format json'...")
    try:
        env = os.environ.copy()
        env["IKUAI_CLI_BASE_URL"] = base_url
        env["IKUAI_CLI_TOKEN"] = token

        process = await asyncio.create_subprocess_exec(
            binary_path, "monitor", "system", "--format", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        stdout, stderr = await process.communicate()

        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout.decode()[:500]}")
        print(f"Stderr: {stderr.decode()[:500]}")

        if process.returncode == 0:
            try:
                data = json.loads(stdout.decode())
                print(f"JSON parsed successfully: {json.dumps(data, indent=2)[:500]}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
        else:
            print(f"Command failed with return code {process.returncode}")

    except Exception as e:
        print(f"Error running command: {e}")
        return False

    # Test users online command
    print("\nTesting 'users online --format json'...")
    try:
        process = await asyncio.create_subprocess_exec(
            binary_path, "users", "online", "--format", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        stdout, stderr = await process.communicate()

        print(f"Return code: {process.returncode}")
        print(f"Stdout: {stdout.decode()[:500]}")
        print(f"Stderr: {stderr.decode()[:500]}")

    except Exception as e:
        print(f"Error running command: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_cli())
    sys.exit(0 if success else 1)