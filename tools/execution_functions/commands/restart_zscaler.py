import asyncio
import os
import subprocess

async def restart_zscaler():
    """
    Stops and then restarts the ZScaler related processes on the endpoint.
    """

    # Determine the current platform (Windows or macOS)
    platform = "windows" if os.name == "nt" else "macos"

    # Define commands based on the platform
    commands = {
        "windows": {
            "stop": "sc stop ZSAService",
            "start": "sc start ZSAService",
            "check": "sc query ZSAService | find \"RUNNING\""
        },
        "macos": {
            "stop": "sudo launchctl stop com.zscaler.zscalerGUI",
            "start": "sudo launchctl start com.zscaler.zscalerGUI",
            "check": "sudo launchctl list | grep com.zscaler.zscalerGUI"
        }
    }

    async def execute_command(cmd: str) -> str:
        """
        Asynchronously executes the given command.
        """
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return stdout.decode(), stderr.decode(), process.returncode

    # Function to validate the service has stopped
    async def validate_service_stopped():
        stdout, _, _ = await execute_command(commands[platform]["check"])
        if platform == "windows":
            return "RUNNING" not in stdout
        else:  # macOS
            return "com.zscaler.zscalerGUI" not in stdout

    # Stop the service with retries
    max_retries = 3
    for i in range(max_retries):
        _, stderr, returncode = await execute_command(commands[platform]["stop"])
        if returncode != 0:
            raise Exception(f"Failed to stop ZScaler service. Error: {stderr}")

        # Check if the service has stopped
        if await validate_service_stopped():
            break
        elif i == max_retries - 1:  # Last retry
            raise Exception("Failed to validate that ZScaler service has stopped after maximum retries.")
        await asyncio.sleep(2)  # Wait 2 seconds before retrying

    # Start the service
    _, stderr, returncode = await execute_command(commands[platform]["start"])
    if returncode != 0:
        raise Exception(f"Failed to start ZScaler service. Error: {stderr}")

    result = asyncio.run(manage_zscaler_service())
    print(result)