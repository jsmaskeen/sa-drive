"""
Provides interactive navigation and mounting commands for SA-Drive:
- navigate: Traverse the folder hierarchy in the terminal.
- mount: Mount the SA-Drive remote locally using gclone.
"""
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import click
from sadrive.helpers.utils import get_parent_id,FF,get_gclone_exe
import sadrive.helpers.dbf as dbf
from typing import List,cast
import inquirer #type:ignore
import subprocess
import re
import time
import os


def navigatehelp(parent_id: str, path: List[str] = []):
    """
    Helper function for navigating through SA-Drive folders.

    Presents an interactive list of current folder's children and handles
    user selection to move into subfolders, go back, or exit.

    Args:
        parent_id: Drive folder ID to list children.
        path: Accumulated path segments for display.

    Returns:
        'exit' to signal termination, None to continue navigation.
    """
    while True:
        choices = [
            FF(i["file_name"], i["_id"], i["parent_id"], i["type"])
            for i in dbf.find_children(parent_id)
        ]
        if len(path) != 0:
            choices.append(FF(".. (back)", "", parent_id, ""))
        choices.append(FF("exit", "", "", ""))

        answer = cast(dict[str,FF],inquirer.prompt(
            [
                inquirer.List(
                    "choice", message=f"Current: /{'/'.join(path)}", choices=choices
                )
            ]
        ))
        choice = answer["choice"]

        if choice.name == "exit":
            return "exit"  
        elif choice.name == ".. (back)":
            path.pop()
            return  
        elif choice.type == 'folder':
            path.append(choice.name)
            result = navigatehelp(choice.file_id, path)
            if result == "exit":
                return "exit" 
        else:
            # click.echo(f"Selected {'file' if choice.type == 'file' else 'folder'}: {choice}, {'file' if choice.type == 'file' else 'folder'} id: {choice.file_id}")
            return "exit"

@click.command()
@click.argument('folderid',default=get_parent_id())
def navigate(folderid:str):
    """
    CLI command to launch interactive navigation of SA-Drive.

    Args:
        folderid: Starting Drive folder ID (defaults to root).

    Behavior:
        Loops until user selects 'exit'. Uses navigatehelp to traverse hierarchy.
    """
    while True:
        result = navigatehelp(folderid)
        if result == "exit":
            break
    return

@click.command()
def mount():
    """
    Mount the SA-Drive remote locally using the gclone tool.

    Detects the assigned drive letter, opens Explorer, and keeps the mount
    until user interrupts (Ctrl+C).

    Side Effects:
        - Runs 'gclone mount' subprocess with vfs caching options.
        - Streams stderr to console to detect mount point.
        - Opens a file browser at the mounted drive letter.
        - Terminates on user interrupt.
    """
    gclone_exe = str(get_gclone_exe())
    cmd = [
        gclone_exe,
        "mount",
        "sadrive:",
        "*",
        "--read-only",
        "--vfs-cache-mode", "full",
        "--vfs-cache-max-size", "1G",
        "--vfs-cache-max-age", "12h",
        "--vfs-read-chunk-size", "64M",
        "--vfs-read-chunk-size-limit", "500M"
    ]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    drive_letter = None
    for line in proc.stderr: #type:ignore
        click.echo(line.rstrip())
        m = re.search(r'Assigning drive letter\s+"([A-Z]:)"', line)
        if m:
            drive_letter = m.group(1)
            break
    
    if drive_letter:
        click.echo(f"Mounted on {drive_letter} - launching Explorer… Press Ctrl+C to stop!")
    else:
        proc.terminate()
        return
    
    
    for _ in range(20):           
        if os.path.isdir(drive_letter):
            break
        time.sleep(0.5)
    else:
        click.echo(f"Unable to open explorer, open manually")
        proc.terminate()
        return
    subprocess.Popen(["explorer", drive_letter])
    
    try:
        proc.wait()
    except KeyboardInterrupt:
        click.echo("\nReceived Ctrl+C, unmounting…")
        proc.terminate()