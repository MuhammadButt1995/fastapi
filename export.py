import os
import json
import plistlib
import asyncio
from pathlib import Path


async def export_bookmarks(browsers=["chrome", "edge", "safari"]):
    """
    Exports bookmarks for the specified browsers.

    Args:
        browsers (list): A list of browser names for which to export bookmarks.
            Supported values: 'chrome', 'edge', 'safari'. Defaults to all three.

    Note:
        The function determines the current OS and browser's data path accordingly.
        For Chrome and Edge, it will look for all profiles and export bookmarks for each.
        The bookmarks are saved in the user's home directory with relevant names.
    """

    # Determine the current platform (Windows or macOS)
    platform = "windows" if os.name == "nt" else "macos"

    # Determine the user's home directory
    user_home = Path.home()

    # Define bookmark file paths for each browser on each supported platform.
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
        "edge": {
            "windows": user_home
            / "AppData"
            / "Local"
            / "Microsoft"
            / "Edge"
            / "User Data",
            "macos": user_home
            / "Library"
            / "Application Support"
            / "Microsoft"
            / "Edge",
        },
        "safari": {"macos": user_home / "Library" / "Safari" / "Bookmarks.plist"},
    }

    def get_profile_name_from_preferences(profile_dir):
        """
        Retrieves the profile name from Chrome/Edge's Preferences file.
        """
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
                print(f"Error reading Preferences for profile in {profile_dir}: {e}")
        return profile_dir.stem

    async def read_and_export(browser, src, dest):
        """
        Reads and exports the bookmarks asynchronously.
        """
        print(f"Attempting to export bookmarks for {browser} from {src} to {dest}")
        try:
            src.rename(src)
        except PermissionError:
            print(
                f"Cannot access {browser} bookmarks. The file might be in use or you lack the necessary permissions."
            )
            return

        if browser in ["chrome", "edge"]:
            try:
                with src.open("r", encoding="utf-8") as f:
                    bookmarks = json.load(f)
                with dest.open("w", encoding="utf-8") as f:
                    json.dump(bookmarks, f, indent=4)
            except Exception as e:
                print(f"Error exporting bookmarks for {browser}: {e}")

        elif browser == "safari":
            try:
                with src.open("rb") as f:
                    bookmarks = plistlib.load(f)
                with dest.open("wb") as f:
                    plistlib.dump(bookmarks, f)
            except Exception as e:
                print(f"Error exporting bookmarks for {browser}: {e}")

    tasks = []

    for browser in browsers:
        print(f"Processing {browser} on {platform}")
        if browser not in paths or platform not in paths[browser]:
            print(f"Cannot export bookmarks for {browser} on {platform}.")
            continue

        if browser in ["chrome", "edge"]:
            browser_data_path = paths[browser][platform]
            print(f"Searching for profiles in {browser_data_path}")
            profiles = [browser_data_path / "Default"] + list(
                browser_data_path.glob("Profile*")
            )

            for profile in profiles:
                source_path = profile / "Bookmarks"
                if source_path.exists():
                    print(f"Found bookmarks for profile {profile}")
                    profile_name = get_profile_name_from_preferences(profile)
                    valid_name = "".join(i for i in profile_name if i not in "\/:*?<>|")
                    destination_path = (
                        user_home / f"{browser}_bookmarks_backup_{valid_name}"
                    )
                    tasks.append(
                        read_and_export(browser, source_path, destination_path)
                    )
                else:
                    print(f"No bookmarks found for profile {profile}")

        elif browser == "safari":
            source_path = paths[browser][platform]
            destination_path = user_home / f"{browser}_bookmarks_backup"
            tasks.append(read_and_export(browser, source_path, destination_path))

    await asyncio.gather(*tasks)


# Calling the function
asyncio.run(export_bookmarks(browsers=["chrome", "edge"]))
