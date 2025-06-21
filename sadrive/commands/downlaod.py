"""
Defines CLI commands for reconstructing split files and downloading
files or folders using 'gclone' with resumable, multi-transfer support.

Commands:

- rebuild(path): Reassemble a split file set into the original file.
- download(id, dest, transfers): Copy from sadrive remote by ID to local path.
"""
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import click
from sadrive.helpers.utils import (
    BUFFER,
    Manifest,
    get_gclone_exe
)
from sadrive.helpers.dbf import get_file_details
from pathlib import Path
import os
import json
import shutil
import subprocess


@click.command()
@click.argument("path")
def rebuild(path: str):
    """
    Rebuilds a file split into ".sapart" parts based on a manifest.

    Args:
        path: Filesystem path to the ".sapart" directory containing part files
              and a ".sapart.manifest.json" manifest.

    Raises:
        FileNotFoundError: If any expected part file is missing during rebuild.
    Side Effects:
        - Reads the manifest to obtain original filename and part order.
        - Concatenates each part into the rebuilt file in the parent directory.
        - Removes the original ".sapart" directory upon success.
    """
    pathp: Path = Path(path).absolute()
    if (path.endswith(".sapart")) and pathp.is_dir():
        manifest_file = [
            f for f in os.listdir(pathp) if f.endswith(".sapart.manifest.json")
        ][0]
        manifest_path = os.path.join(pathp, manifest_file)
        with open(manifest_path, "r") as mf:
            manifest: Manifest = json.load(mf)

        original_filename = manifest["original_filename"]
        parent_dir = os.path.dirname(os.path.abspath(pathp))
        rebuilt_file_path = os.path.join(parent_dir, original_filename)
        with open(rebuilt_file_path, "wb") as out_file:
            for part in manifest["parts"]:
                part_path = os.path.join(pathp, part["filename"])
                if not os.path.exists(part_path):
                    raise FileNotFoundError(f"Missing part file: {part_path}")
                with open(part_path, "rb") as pf:
                    while True:
                        chunk = pf.read(BUFFER)
                        if not chunk:
                            break
                        out_file.write(chunk)
        shutil.rmtree(pathp)
        
@click.command()
@click.argument("id")
@click.argument("dest", type=click.Path(exists=False, file_okay=False, dir_okay=True))
@click.option("--transfers", "-t", default=8, show_default=True, help="Number of concurrent transfers")
def download(id: str, dest: str, transfers: int):
    """
    Downloads a folder from the 'sadrive' remote by its ID.

    Uses the gclone executable configured via config to perform a multi-threaded
    copy with progress display.

    Args:
        id: The Drive folder ID to copy from the remote.
        dest: Local destination directory path.
        --transfers: Number of parallel transfer threads (default 8).

    Side Effects:
        - Invokes the gclone subprocess with constructed arguments.
        - Prints success or error messages on completion.
    """
    fd = get_file_details(id)
    if (not fd) or fd["type"] == "file":
        click.echo("Juse the web ui to download the file. Use this command only for folders.")
        return 
    gclone = str(get_gclone_exe())
    source = f"sadrive:{{{id}}}"
    cmd = [
        gclone,
        "copy",
        source,
        dest,
        "--progress",
        "--transfers", str(transfers)
    ]
    try:
        subprocess.run(cmd, check=True)
        click.echo("Downloaded successfully! If there are .sapart folders, then run the rebuild command to combine them!")
    except subprocess.CalledProcessError as e:
        click.echo("Download failed:")
        click.echo(e.stderr or e.stdout)