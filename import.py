import os
import json
import plistlib
import asyncio
from pathlib import Path

async def import_bookmarks(browsers=['chrome', 'edge', 'safari']):
    """
    Imports bookmarks for the specified browsers based on the current OS.
    
    Args:
        browsers (list): List of browser names for which to import bookmarks.
            Supported values: 'chrome', 'edge', 'safari'. Defaults to all three.
    """

    # Determine the current platform
    platform = 'windows' if os.name == 'nt' else 'macos'
    user_home = Path.home()

    # Define bookmark paths based on the browser and platform
    paths = {
        'chrome': {
            'windows': user_home / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data',
            'macos': user_home / 'Library' / 'Application Support' / 'Google' / 'Chrome'
        },
        'edge': {
            'windows': user_home / 'AppData' / 'Local' / 'Microsoft' / 'Edge' / 'User Data',
            'macos': user_home / 'Library' / 'Application Support' / 'Microsoft' / 'Edge'
        },
        'safari': {
            'macos': user_home / 'Library' / 'Safari' / 'Bookmarks.plist'
        }
    }

    async def restore_backup(browser, backup_file, dest):
        """Restores the bookmarks from a backup file to the destination."""
        print(f"Attempting to import bookmarks for {browser} from {backup_file} to {dest}")
        try:
            if dest.parent.exists():
                if browser in ['chrome', 'edge']:
                    with backup_file.open('r', encoding='utf-8') as f:
                        bookmarks = json.load(f)
                    with dest.open('w', encoding='utf-8') as f:
                        json.dump(bookmarks, f, indent=4)
                elif browser == 'safari':
                    with backup_file.open('rb') as f:
                        bookmarks = plistlib.load(f)
                    with dest.open('wb') as f:
                        plistlib.dump(bookmarks, f)
            else:
                print(f"Profile directory {dest.parent} does not exist. Skipping...")
        except Exception as e:
            print(f"Error importing bookmarks for {browser}: {e}")

    def get_existing_profile_name(profile_dir):
        """Retrieves the profile name from Chrome/Edge's Preferences file."""
        preferences_path = profile_dir / 'Preferences'
        if preferences_path.exists():
            try:
                with preferences_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('profile', {}).get('name') or data.get('account_info', [{}])[0].get('full_name') or profile_dir.stem
            except Exception as e:
                print(f"Error reading Preferences for profile in {profile_dir}: {e}")
        return profile_dir.stem

    tasks = []

    for browser in browsers:
        print(f"Processing {browser} on {platform}")
        if browser not in paths or platform not in paths[browser]:
            print(f"Cannot import bookmarks for {browser} on {platform}.")
            continue

        if browser in ['chrome', 'edge']:
            browser_data_path = paths[browser][platform]
            existing_profiles = [browser_data_path / 'Default'] + list(browser_data_path.glob('Profile*'))
            existing_profile_names = {
                get_existing_profile_name(profile): profile for profile in existing_profiles
            }

            backup_files = list(user_home.glob(f"{browser}_bookmarks_backup_*"))
            for backup in backup_files:
                profile_name_from_backup = backup.stem.split('_')[-1]
                
                profile_folder = existing_profile_names.get(profile_name_from_backup)
                if profile_folder:
                    dest_path = profile_folder / 'Bookmarks'
                    tasks.append(restore_backup(browser, backup, dest_path))
                else:
                    print(f"Profile {profile_name_from_backup} not found in {browser} installation. Skipping...")

        elif browser == 'safari':
            backup_file = user_home / f"{browser}_bookmarks_backup"
            dest_path = paths[browser][platform]
            tasks.append(restore_backup(browser, backup_file, dest_path))

    await asyncio.gather(*tasks)

# Run the main function for importing bookmarks
asyncio.run(import_bookmarks(browsers=['chrome', 'edge']))