"""
This module provides helper functions and utilities for the CLI application.
It uses service account storage for Google Drive operations and offers:

- Configuration directory handling
- Path construction for accounts and database
- Rclone configuration initialization
- Human-readable byte and time formatting
- List partitioning
- Generator wrapper
- Service account selection by free space
- Directory tree mapping
- File size measurement
- Filename shortening

Constants:
- CONFIG_POINTER: Path to the file storing the config directory pointer
- MAGIC_SIZE: Total capacity threshold for service accounts (in bytes)
- BUFFER: Buffer size threshold (in bytes)
- MAX_THREADS: Maximum number of threads permitted
"""
from pathlib import Path
import time
import os
from math import ceil
from typing import List, TypeVar,Any,Union, Dict,TypedDict
import json

T = TypeVar('T')

DirTree = Dict[str, Union['DirTree', int]]

class PartInfo(TypedDict):
    """
    Information about a part of a split file.

    Attributes:
        filename: Name of the file part.
        size: Size of the file part in bytes.
    """
    filename: str
    size: int

class Manifest(TypedDict):
    """
    Manifest describing an original file and its parts.

    Attributes:
        original_filename: The original filename before splitting.
        parts: A list of PartInfo dictionaries for each part.
    """
    original_filename: str
    parts: List[PartInfo]

class FF:
    """
    Represents a file or folder entry in Google Drive.

    Attributes:
        name: The display name of the file or folder.
        file_id: The unique identifier in Drive.
        parent_id: The parent folder's identifier.
        type: The entry type, e.g. 'folder' or 'file'.
    """
    def __init__(self, name: str, file_id: str, parent_id: str, type: str) -> None:
        """
        Initializes an FF object.

        Args:
            name: Display name of the file/folder.
            file_id: Unique identifier in Drive.
            parent_id: Identifier of the parent folder.
            type: 'folder' or 'file'.
        """
        self.name = name
        self.file_id = file_id
        self.parent_id = parent_id
        self.type = type

    def __repr__(self):
        """
        Returns a human-readable representation of the entry.

        Returns:
            A formatted string including type, ID, and name.
        """
        if self.type != "":
            return f"[{self.type.rjust(6)}] [{self.file_id}] {self.name}"
        return self.name

CONFIG_POINTER = Path.home() / ".sadrive_config_dir"
MAGIC_SIZE = 15784004812
BUFFER = 250 * 1024 * 1024
MAX_THREADS = 10

def get_config_dir() -> Path:
    """
    Retrieves the configuration directory path from CONFIG_POINTER.

    Raises:
        RuntimeError: If the pointer file is missing or the stored path is invalid.

    Returns:
        Path: The directory used for storing application config files.
    """
    if CONFIG_POINTER.exists():
        config_dir = Path(CONFIG_POINTER.read_text().strip())
        if config_dir.is_dir():
            return config_dir
        else:
            raise RuntimeError(f"Stored config dir {config_dir} does not exist. Run `sadrive config set-dir <path>`")
    raise RuntimeError(
        "No config directory set. Run `sadrive config set-dir <path>` first."
    )


def get_accounts_path() -> Path:
    """
    Constructs the path to the 'accounts' subdirectory within the config directory.

    Returns:
        Path: Path to the service accounts directory.
    """
    return Path.joinpath(get_config_dir(), "accounts")


def get_database_path() -> Path:
    """
    Constructs the path to the SQLite database file within the config directory.

    Returns:
        Path: Path to the 'database.db' file.
    """
    return Path.joinpath(get_config_dir(), "database.db")

def get_parent_id() -> str:
    """
    Reads and returns the parent folder ID from config.json.

    Returns:
        str: The 'parent_id' value stored in config.json.
    """
    with open(Path.joinpath(get_config_dir(),'config.json')) as f:
        parent_id:str = json.load(f)['parent_id']
    return parent_id

def get_gclone_exe() -> Path:
    """
    Reads and returns the path to the gclone executable from config.json.

    Returns:
        Path: Path to the 'gclone' executable.
    """
    with open(Path.joinpath(get_config_dir(),'config.json')) as f:
        path:Path = Path(json.load(f)['path_to_gclone.exe'])
    return path

def set_rclone_conf():
    """
    Creates rcone.conf next to gclone executable with default content using the first service account.
    """
    gcpath_parent = get_gclone_exe().parent
    confpath = gcpath_parent.joinpath('rclone.conf')
    with open(confpath,'w') as f:
        f.write(f'''[sadrive]
type = drive  
scope = drive  
service_account_file = {get_accounts_path().joinpath('0.json')}
service_account_file_path = {get_accounts_path()}
root_folder_id = {get_parent_id()}''')

def humanbytes(size: float) -> str:
    """
    Converts a size in bytes to a human-readable string.

    Args:
        size: Size in bytes.

    Returns:
        str: Formatted size (e.g. '1.234 MiB').
    """
    if not size:
        return ""
    power = 2**10
    number = 0
    dict_power_n = {0: " ", 1: "K", 2: "M", 3: "G", 4: "T", 5: "P"}
    while size > power:
        size /= power
        number += 1
    return str(round(size, 3)) + " " + dict_power_n[number] + "iB"


def humantime(seconds: int):
    """
    Formats a duration in seconds into HhMmSs or MmSs.

    Args:
        seconds: Duration in seconds.

    Returns:
        str: Formatted time string.
    """
    if seconds > 3600:
        return time.strftime("%Hh%Mm%Ss", time.gmtime(seconds))
    else:
        return time.strftime("%Mm%Ss", time.gmtime(seconds))


def list_into_n_parts(lst: List[T], n: int) -> List[List[T]]:
    """
    Splits a list into n approximately equal parts.

    Args:
        lst: List of items to split.
        n: Number of parts.

    Returns:
        List[List[T]]: A list containing n sublists.
    """
    size = ceil(len(lst) / n)
    return [lst[i * size : i * size + size] for i in range(n)]


class Generator:
    """
    Wrapper to enable 'yield from' for a generator function.

    Attributes:
        gen: The underlying generator.
    """
    def __init__(self, gen:Any):
        """
        Initializes the Generator wrapper.

        Args:
            gen: A generator object.
        """
        self.gen = gen

    def __iter__(self): #type: ignore
        """
        Enables iteration by delegating to the underlying generator.

        Yields:
            Any: Values produced by the generator.
        """
        self.value:Any = yield from self.gen

def get_free_sa(sa_map:List[dict[str,Any]],file_size:int):
    """
    Selects service account IDs with enough free space.

    Args:
        sa_map: List of dicts containing '_id' and 'size' keys.
        file_size: Required file size in bytes.

    Returns:
        List[int]: Sorted list of account IDs that can accommodate the file.
    """
    tmp:List[List[int]] = []
    for i in sa_map:
        if MAGIC_SIZE - int(i['size']) >=file_size:
            tmp.append([int(i['size']),int(i['_id'])])
    tmp.sort(key=lambda x:x[0])
    ok_sas = [i[1] for i in tmp]
    return ok_sas

def get_dir_structure(path: Path) -> DirTree:
    """
    Recursively builds a directory tree mapping folder names to subtrees or file sizes.

    Args:
        path: Root directory path.

    Returns:
        DirTree: Nested dict mapping names to file sizes or further DirTrees.
    """
    def helper(current_path:Path) -> DirTree:
        structure:DirTree = {}
        for entry in os.listdir(current_path):
            full_path = Path.joinpath(current_path, entry)
            if os.path.isdir(full_path):
                structure[entry] = helper(full_path)
            else:
                file_size = os.path.getsize(full_path)
                structure[entry] = file_size
        return structure

    return {os.path.basename(path): helper(path)}

def get_file_size(file_path:Path):
    """
    Returns the size of a file in bytes by seeking to its end.

    Args:
        file_path: Path to the target file.

    Returns:
        int: File size in bytes.
    """
    with open(file_path, 'rb') as stream_bytes:
        stream_bytes.seek(0, 2)
        size = stream_bytes.tell()
    return size

def shorten_fn(name: str, max_len: int = 75) -> str:
    """
    Truncates a filename to a maximum length with an ellipsis in the middle.

    Args:
        name: Original filename.
        max_len: Maximum allowed length.

    Returns:
        str: Shortened filename if needed, else original.
    """
    if len(name) <= max_len:
        return name
    if max_len < 5:
        return name[:max_len]
    head_len = max_len - max_len // 2
    tail_start = len(name) - (max_len // 2)
    head = name[:head_len]
    tail = name[tail_start:]
    return f"{head}...{tail}"