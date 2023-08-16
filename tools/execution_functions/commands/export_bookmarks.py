from typing import Any
import os
import json
import plistlib
import asyncio
from pathlib import Path
import aiofiles


async def export_bookmarks(**params: Any):
    """
    Exports bookmarks for the specified browsers.
    """

    # Retrieve browsers from params or set default value to Chrome
    browser_param = params.get("browser", params.get("browsers", "chrome"))
    browsers = browser_param.split(",")

    # Determine the current platform (Windows or macOS)
    platform = "windows" if os.name == "nt" else "macos"

    # Determine the user's home directory
    user_home = Path.home()

    # Determine the user's OneDrive directory for saving exported bookmarks
    user_onedrive = (
        user_home / "Fannie Mae" / "OneDrive - Fannie Mae"
        if platform == "windows"
        else user_home / "OneDrive - Fannie Mae"
    )

    # Define bookmark source file paths for each browser on each supported platform.
    paths = {
        "chrome": {
            "windows": user_home
            / "AppData"
            / "Local"
            / "Google"
            / "Chrome"
            / "User Data",
            "macos": user_home
            / "Library"
            / "Application Support"
            / "Google"
            / "Chrome",
        },
        "safari": {"macos": user_home / "Library" / "Safari" / "Bookmarks.plist"},
    }

    def get_profile_name_from_preferences(profile_dir: Path) -> str:
        """
        Retrieves the profile name from Chrome's Preferences file.
        """
        preferences_path = profile_dir / "Preferences"
        if preferences_path.exists():
            try:
                with open(preferences_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return (
                    data.get("profile", {}).get("name")
                    or data.get("account_info", [{}])[0].get("full_name")
                    or profile_dir.stem
                )
            except Exception as e:
                raise ValueError(
                    f"Error reading Preferences for profile in {profile_dir}: {e}"
                )
        return profile_dir.stem

    async def read_and_export(browser: str, src: Path, dest: Path):
        """
        Reads and exports the bookmarks asynchronously using aiofiles.
        """
        if browser == "chrome":
            try:
                async with aiofiles.open(src, mode="r", encoding="utf-8") as f:
                    bookmarks = await f.read()
                bookmarks_json = json.loads(bookmarks)
                async with aiofiles.open(dest, mode="w", encoding="utf-8") as f:
                    await f.write(json.dumps(bookmarks_json, indent=4))
            except Exception as e:
                raise ValueError(f"Error exporting bookmarks for {browser}: {e}")

        elif browser == "safari":
            try:
                async with aiofiles.open(src, mode="rb") as f:
                    bookmarks = await f.read()
                bookmarks_plist = plistlib.loads(bookmarks)
                async with aiofiles.open(dest, mode="wb") as f:
                    await f.write(plistlib.dumps(bookmarks_plist))
            except Exception as e:
                raise ValueError(f"Error exporting bookmarks for {browser}: {e}")

    tasks = []

    for browser in browsers:
        if browser not in paths or platform not in paths[browser]:
            raise ValueError(f"Cannot export bookmarks for {browser} on {platform}.")

        if browser == "chrome":
            browser_data_path = paths[browser][platform]
            # Dynamically detect all profile directories
            profiles = list(browser_data_path.glob("Profile*"))
            if (browser_data_path / "Default").exists():
                profiles.append(browser_data_path / "Default")

            for profile in profiles:
                source_path = profile / "Bookmarks"
                if source_path.exists():
                    profile_name = get_profile_name_from_preferences(profile)
                    valid_name = "".join(i for i in profile_name if i not in "\/:*?<>|")
                    destination_path = (
                        user_onedrive / f"{browser}_bookmarks_backup_{valid_name}.json"
                    )
                    tasks.append(
                        read_and_export(browser, source_path, destination_path)
                    )
                else:
                    raise ValueError(f"No bookmarks found for profile {profile}")

        elif browser == "safari":
            source_path = paths[browser][platform]
            destination_path = user_onedrive / f"{browser}_bookmarks_backup.plist"
            tasks.append(read_and_export(browser, source_path, destination_path))

    await asyncio.gather(*tasks)
