import subprocess
import platform


async def reset_dns():
    cmd = None

    # Determine the OS and set the appropriate command
    system_platform = platform.system()
    if system_platform == "Windows":
        cmd = ["ipconfig", "/flushdns"]
    else:  # macOS
        cmd = ["sudo", "killall", "-HUP", "mDNSResponder"]

    # Try creating a new subprocess and run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Clean and format the output
        formatted_output = "\n".join(
            [line.strip() for line in result.stdout.splitlines() if line.strip()]
        )

        return f"Successfully reset DNS. Output:\n\n{formatted_output}"
    except subprocess.CalledProcessError as e:
        raise Exception(
            f"Failed to reset DNS. Command: {cmd}. Error: {e.stderr.strip()}"
        )
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error"
        raise Exception(
            f"Failed to initiate subprocess for command {cmd}. Error: {error_detail}"
        )
