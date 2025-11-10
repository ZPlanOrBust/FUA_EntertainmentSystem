from pathlib import Path
import os

def get_base_root_path(full_relative_path: str | None, media_folders: list[str]):
    if not full_relative_path:
        return None
    if full_relative_path in [Path(p).name for p in media_folders]:
        for root_folder in media_folders:
            if Path(root_folder).name == full_relative_path:
                return Path(root_folder)
        return None
    root_name = Path(full_relative_path).parts[0]
    for root_folder in media_folders:
        root_path = Path(root_folder)
        if root_path.name == root_name:
            return root_path
    return None

def resolve_absolute_path(media_path: str, media_folders: list[str]):
    base_root_path = get_base_root_path(media_path, media_folders)
    if not base_root_path:
        return None
    if media_path == base_root_path.name:
        return base_root_path
    path_parts_to_append = Path(media_path).parts[1:]
    candidate_path = base_root_path
    for part in path_parts_to_append:
        candidate_path = candidate_path / part
    if candidate_path.exists():
        return candidate_path
    return None
