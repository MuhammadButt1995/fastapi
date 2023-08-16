from typing import Any
import os
import json
import plistlib
import asyncio
from pathlib import Path


async def import_bookmarks(**params: Any):
    """
    Imports bookmarks for the specified browsers based on the current OS.
    """
    # Retrieve browsers from params or set default value to Chrome
    browser_param = params.get("browser", params.get("browsers", "chrome"))
    browsers = browser_param.split(",")

    # Determine the current platform
    platform = "windows" if os.name == "nt" else "macos"
    user_home = Path.home()
    user_onedrive = (
        user_home / "Fannie Mae" / "OneDrive - Fannie Mae"
        if platform == "windows"
        else user_home / "OneDrive - Fannie Mae"
    )

    # Define bookmark paths based on the browser and platform
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

    async def restore_backup(browser, backup_file, dest):
        """Restores the bookmarks from a backup file to the destination."""
        try:
            if not dest.parent.exists():
                raise ValueError(
                    f"Profile directory {dest.parent} does not exist for {browser}."
                )

            if browser == "chrome":
                with backup_file.open("r", encoding="utf-8") as f:
                    bookmarks = json.load(f)
                with dest.open("w", encoding="utf-8") as f:
                    json.dump(bookmarks, f, indent=4)
            elif browser == "safari":
                with backup_file.open("rb") as f:
                    bookmarks = plistlib.load(f)
                with dest.open("wb") as f:
                    plistlib.dump(bookmarks, f)
        except Exception as e:
            raise ValueError(f"Error importing bookmarks for {browser}: {e}")

    def get_existing_profile_name(profile_dir):
        """Retrieves the profile name from Chrome's Preferences file."""
        preferences_path = profile_dir / "Preferences"
        if preferences_path.exists():
            try:
                with preferences_path.open("r", encoding="utf-8") as f:
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

    tasks = []

    for browser in browsers:
        if browser not in paths or platform not in paths[browser]:
            raise ValueError(f"Cannot import bookmarks for {browser} on {platform}.")

        if browser == "chrome":
            browser_data_path = paths[browser][platform]

            # Dynamically detect all profile directories
            existing_profiles = list(browser_data_path.glob("Profile*"))
            if (browser_data_path / "Default").exists():
                existing_profiles.append(browser_data_path / "Default")

            existing_profile_names = {
                get_existing_profile_name(profile): profile
                for profile in existing_profiles
            }

            # Search for backup files in OneDrive
            backup_files = list(user_onedrive.glob(f"{browser}_bookmarks_backup_*"))
            if not backup_files:
                raise FileNotFoundError(
                    f"No backup files found in OneDrive for {browser}!"
                )

            for backup in backup_files:
                profile_name_from_backup = backup.stem.split("_")[-1]

                profile_folder = existing_profile_names.get(profile_name_from_backup)
                if profile_folder:
                    dest_path = profile_folder / "Bookmarks"
                    tasks.append(restore_backup(browser, backup, dest_path))
                else:
                    raise ValueError(
                        f"Profile {profile_name_from_backup} not found in {browser} installation."
                    )

        elif browser == "safari":
            backup_file = user_onedrive / f"{browser}_bookmarks_backup"
            if not backup_file.exists():
                raise FileNotFoundError(
                    f"No backup file found in OneDrive for {browser}!"
                )

            dest_path = paths[browser][platform]
            tasks.append(restore_backup(browser, backup_file, dest_path))

    await asyncio.gather(*tasks)
