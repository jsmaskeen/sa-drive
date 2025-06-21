"""
Handles uploading files and directories to SA-Drive, including:

- Splitting large files across multiple service accounts based on available space
- Preparing and writing ".sapart" parts and manifest files for oversized uploads
- Reflecting local directory structures on the remote Drive
- Concurrent uploading with progress tracking via Rich
- Recursive and single-file upload commands integrated with Click

Key components:
- `prepare_sapart_jobs`: Divides a large file into parts and records upload jobs
- `upload_file`: Streams a file or part to Drive with real-time progress updates
- `sem_upload_wrapper`: Ensures semaphore-based concurrency control for threads
- `reflect_structure_on_sadrive`: Mirrors a local directory tree to remote folders
- `upload` command: CLI entry point orchestrating directory or file uploads
"""
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import click
from sadrive.helpers.utils import (
    get_parent_id,
    get_dir_structure,
    get_free_sa,
    Generator,
    get_file_size,
    DirTree,
    MAGIC_SIZE,
    BUFFER,
    MAX_THREADS,
    Manifest,
    shorten_fn
)
from click import Context
from sadrive.helpers.drive import SADrive
from pathlib import Path
import os
from threading import Thread, Semaphore
import sadrive.helpers.dbf as dbf
from typing import Any, Dict, Union, cast
from sadrive.commands.navigate import navigate
import json
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskID,
    DownloadColumn,
    TransferSpeedColumn,
)
from rich.table import Column as TableColumn
import logging

import time

logging.basicConfig(
    filename="upload.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

sem = Semaphore(MAX_THREADS)


class UploadThread(Thread):
    """
    Thread subclass that captures the return value of its target function.

    Attributes:
        _return: The value returned by the target function after execution.

    Methods:
        run(): Executes the target function and stores its return value.
        join(timeout): Joins the thread and returns the stored return value.
    """
    def __init__(
        self,
        group: Any = None,
        target: Any = None,
        name: Any = None,
        args: Any = (),
        kwargs: Any = {},
    ):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return: Any = None

    def run(self):
        """
        Runs the thread, invoking the target function and storing its result.
        """
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, timeout: Any = None):
        """
        Waits for the thread to finish and returns the function's return value.

        Args:
            timeout: Optional timeout in seconds.

        Returns:
            The return value from the target function.
        """
        Thread.join(self, timeout)
        return self._return


def prepare_sapart_jobs(
    file_path: str, total_size: int, parent_folder_id: str
) -> list[tuple[str, int, str, str]]:
    """
    Prepare split-upload jobs for a large file that exceeds single-account capacity.

    Args:
        file_path: Local filesystem path to the source file.
        total_size: Total size of the source file in bytes.
        parent_folder_id: Drive folder ID where the parts will be uploaded.

    Returns:
        List of tuples describing each upload job. Each tuple contains:
        - part_file_path (str): Path to the generated part file.
        - part_size (int): Size of this part in bytes.
        - service_account_id (str): ID of the service account chosen for this part.
        - remote_folder_id (str): Drive folder ID for uploading this part.
    """
    size_map = dbf.get_size_map()
    partial_sas: list[tuple[int, int]] = []
    empty_sas: list[tuple[int, int]] = []
    for rec in size_map:
        sa_id, used = rec["_id"], rec["size"]
        free = MAGIC_SIZE - used
        if used > 0 and free > 0:
            partial_sas.append((sa_id, free))
        elif used == 0:
            empty_sas.append((sa_id, free))

    candidate_sas: list[tuple[int, int]] = []
    remaining = total_size
    partial_sas.sort(key=lambda c: c[1])
    for sa_id, free in partial_sas:
        if remaining <= 0:
            break
        chunk = min(free, remaining)
        candidate_sas.append((sa_id, chunk))
        remaining -= chunk

    it = iter(empty_sas)
    while remaining > 0:
        try:
            sa_id, free = next(it)
        except StopIteration:
            raise RuntimeError("Not enough SA space!")
        chunk = min(free, remaining)
        candidate_sas.append((sa_id, chunk))
        remaining -= chunk

    folder_name = os.path.basename(file_path) + ".sapart"
    drive = SADrive("0")
    sapart_folder_id = drive.create_folder(folder_name, parent_folder_id)

    jobs: list[tuple[str, int, str, str]] = []
    with open(file_path, "rb") as src:
        for idx, (sa_id, chunk_size) in enumerate(candidate_sas, start=1):
            part_name = f"{os.path.basename(file_path)}.sapart{idx}"
            with open(part_name, "wb") as dst:
                to_go = chunk_size
                while to_go > 0:
                    buf = src.read(min(BUFFER, to_go))
                    dst.write(buf)
                    to_go -= len(buf)
            print(f"Prepared {part_name}: {chunk_size} bytes → SA {sa_id}")

            jobs.append((part_name, chunk_size, sapart_folder_id, str(sa_id)))

    manifest: Manifest = {
        "original_filename": os.path.basename(file_path),
        "parts": [
            {"filename": f"{os.path.basename(file_path)}.sapart{idx}", "size": size}
            for idx, (_, size) in enumerate(candidate_sas, start=1)
        ],
    }
    mname = os.path.basename(file_path) + ".sapart.manifest.json"
    with open(mname, "w") as mf:
        json.dump(manifest, mf, indent=2)
    jobs.append((mname, os.path.getsize(mname), sapart_folder_id, "-1"))
    print(f"Prepared manifest: {mname}")
    return jobs


def upload_file(
    file_path: str,
    size: int,
    parent_folder_id: str,
    progress: Progress,
    task_id: int,
    sa_num_provided: str = "",
) -> Dict[str, Union[str, int]]:
    """
    Upload a file or part to SA-Drive, streaming with progress tracking.

    Args:
        file_path: Local path to the file or part to upload.
        size: Total size of the upload in bytes.
        parent_folder_id: Drive folder ID where the file will be stored.
        progress: Rich Progress instance for updating the progress bar.
        task_id: Task identifier for Rich progress updates.
        sa_num_provided: Optional service account ID to use; if empty, choose automatically.

    Returns:
        Dict containing details of the uploaded file from the Drive API response,
        including 'id', 'title', 'parents', and 'fileSize'.
    """
    start = time.time()
    last_bytes = 0
    if sa_num_provided == "":
        sa_numbers = get_free_sa(dbf.get_size_map(), size)
        sa_number = str(sa_numbers[0])
    else:
        sa_number = sa_num_provided
    drive = SADrive(sa_number)
    with open(file_path, "rb") as stream_bytes:
        filename = os.path.basename(file_path)
        worker = Generator(drive.upload_file(filename, parent_folder_id, stream_bytes))
        for prog in worker:
            bytes_done = int(prog / 100 * size)
            delta = bytes_done - last_bytes
            last_bytes = bytes_done
            
            elapsed = time.time() - start
            speed = bytes_done / elapsed if elapsed > 0 else 0
            progress.update(cast(TaskID, task_id), advance=delta)
            logging.debug(
                f"{file_path}: {prog:.1f}% → " f"{bytes_done}/{size} B, {speed:.2f} B/s"
            )
        
        if last_bytes < size:
            progress.update(cast(TaskID, task_id), advance=(size - last_bytes))

    uled_file_details = worker.value

    dbf.insert_file(
        uled_file_details["id"],
        uled_file_details["title"],
        uled_file_details["parents"][0]["id"],
        int(uled_file_details["fileSize"]),
        "file",
        str(sa_number),
        False,
    )
    return uled_file_details


def sem_upload_wrapper(
    fp: str, sz: int, pid: str, progress: Progress, task_id: int, sa: str
):
    """
    Wrapper for uploading a file that ensures semaphore release after completion.

    Args:
        fp: Local file path to upload.
        sz: File size in bytes.
        pid: Drive parent folder ID.
        progress: Rich Progress instance for tracking upload progress.
        task_id: Identifier for the progress task.
        sa: Service account ID to use for this upload.

    Behavior:
        - Calls `upload_file` with provided arguments.
        - Ensures the global `sem` is released even if an error occurs.
    """
    try:
        upload_file(fp, sz, pid, progress, task_id, sa)
    finally:
        sem.release()


def reflect_structure_on_sadrive(
    structure: DirTree,
    destination: str,
    parent_id_map: list[tuple[str, int, str]],
    tmp_drive: SADrive,
    path: list[str],
):
    """
    Recursively reflect a local directory tree structure on SA-Drive by creating folders and scheduling file uploads.

    Args:
        structure: Nested dictionary mapping folder names to subtrees or file sizes.
        destination: Drive folder ID where this level's content should be mirrored.
        parent_id_map: List tracking tuples of (folder_name, local_size, drive_folder_id) for created folders.
        tmp_drive: Authenticated SADrive instance used for folder creation.
        path: Accumulated list of path segments representing the current traversal.

    Behavior:
        - Iterates through the `structure` dict:
          - For sub-dictionaries, creates a corresponding folder on Drive, updates `parent_id_map`, and recurses.
          - For file entries (size values), schedules upload jobs for each file part.
        - Does not perform actual uploads; integrates with the main `upload` command logic.
    """
    for key, value in structure.items():
        if isinstance(value, int):
            path.append(key)
            parent_id_map.append(("\\".join(path), value, destination))
            path.pop()
        else:  # Value is dirtree
            nf_id = tmp_drive.create_folder(key, destination)
            dbf.insert_file(nf_id, key, destination, 0, "folder", "0", False)
            path.append(key)
            reflect_structure_on_sadrive(value, nf_id, parent_id_map, tmp_drive, path)
            path.pop()
    return


@click.command()
@click.argument("path")
@click.argument("destination", default=get_parent_id())
@click.pass_context
def upload(ctx: Context, path: str, destination: str):
    """
    Upload a folder or file to SA-Drive at a specified destination folder ID.

    Args:
        ctx: Click context for invoking subcommands.
        path: Local filesystem path to the file or directory to upload.
        destination: Drive folder ID where the content will be uploaded (default: root).

    Behavior:
        - Determines if `path` is a file or directory.
        - For files larger than single-account capacity, splits into parts and uploads.
        - For directories, reflects structure on SA-Drive and uploads all contents.
        - Updates local database mappings and service account usage.
        - Provides real-time progress via Rich.
    """
    fd = dbf.get_file_details(destination)
    if destination != get_parent_id():
        if (not fd) or fd["type"] == "file":
            click.echo("Destination folder id does not exist !!")
            return
    pathp: Path = Path(path).absolute()

    progress = Progress(
        SpinnerColumn(table_column=TableColumn("")),
        TextColumn("[bold blue]{task.fields[filename]}", 
               table_column=TableColumn("File"), justify="right"),
        BarColumn(table_column=TableColumn("Progress")),
        DownloadColumn(binary_units=True,table_column=TableColumn("Size")),
        TransferSpeedColumn(table_column=TableColumn("Speed")), 
        TimeElapsedColumn(table_column=TableColumn("Elapsed")),
        TimeRemainingColumn(table_column=TableColumn("ETA")),  
    )
    progress.start()

    if Path.is_dir(pathp):
        structure = get_dir_structure(pathp)
        # (filepath,size,parent_id)
        parent_id_map: list[tuple[str, int, str]] = []
        spath: list[str] = [".."]
        tmp_drive: SADrive = SADrive("0")
        reflect_structure_on_sadrive(
            structure, destination, parent_id_map, tmp_drive, spath
        )
        parent_id_map.sort(key=lambda x: x[1])
        sa_map_copy = [[i["_id"], i["size"]] for i in dbf.get_size_map()]
        file_sa_num_map: dict[str, str] = {}
        # filepath - sanumber
        upload_threads: list[UploadThread] = []
        large_files: list[tuple[str, int, str]] = []

        for file_path, size, dest_id in parent_id_map:
            candidates: list[tuple[int, str, int, int]] = []
            for idx, (sa_id, used) in enumerate(sa_map_copy):
                free = MAGIC_SIZE - used
                if free >= size:
                    candidates.append((idx, sa_id, used, free - size))

            if not candidates:
                large_files.append((file_path, size, dest_id))
                continue
                # raise RuntimeError(f"Cannot assign file {file_path}, size {size}: no SA has enough space.")

            best_idx, best_sa_id, _, _ = min(candidates, key=lambda x: x[3])

            sa_map_copy[best_idx][1] += size
            file_sa_num_map[file_path] = best_sa_id

            task_id = progress.add_task("", total=size, filename=shorten_fn(file_path))
            sem.acquire()
            t = UploadThread(
                target=sem_upload_wrapper,
                args=(
                    pathp.joinpath(file_path).resolve(),
                    size,
                    dest_id,
                    progress,
                    task_id,
                    best_sa_id,
                ),
            )
            upload_threads.append(t)
            t.start()

        for fp, sz, did in large_files:
            jobs = prepare_sapart_jobs(str(pathp.joinpath(fp).resolve()), sz, did)
            for job in jobs:
                # job == (part_path, part_size, sapart_folder_id, sa_id)
                task_id = progress.add_task("", total=sz, filename=shorten_fn(fp))
                sem.acquire()
                jj: list[Any] = cast(Any, list(job))
                if job[-1] == "-1":
                    jj[-1] = progress
                    jj.append(task_id)
                    jj.append("")
                else:
                    sasa = jj[-1]
                    jj[-1] = progress
                    jj.append(task_id)
                    jj.append(sasa)

                t = UploadThread(target=sem_upload_wrapper, args=tuple(jj))
                upload_threads.append(t)
                t.start()

        for x in upload_threads:
            x.join()

    else:

        sz = get_file_size(pathp)
        if sz > MAGIC_SIZE:
            upload_threads: list[UploadThread] = []
            jobs = prepare_sapart_jobs(str(pathp), sz, destination)

            for job in jobs:
                # job == (part_path, part_size, sapart_folder_id, sa_id)
                task_id = progress.add_task("", total=job[1], filename=shorten_fn(job[0]))
                sem.acquire()
                jj: list[Any] = cast(Any, list(job))
                if job[-1] == "-1":
                    jj[-1] = progress
                    jj.append(task_id)
                    jj.append("")
                else:
                    sasa = jj[-1]
                    jj[-1] = progress
                    jj.append(task_id)
                    jj.append(sasa)
                t = UploadThread(target=sem_upload_wrapper, args=tuple(jj))
                upload_threads.append(t)
                t.start()

            for x in upload_threads:
                x.join()

        else:
            task_id = progress.add_task("", total=sz, filename=shorten_fn(str(pathp)))
            t = UploadThread(
                target=upload_file,
                args=(pathp, sz, destination, progress, task_id, ""),
            )
            t.start()
            t.join()
    progress.stop()
    click.echo("Uploaded the file/folder! Navigate it:")
    ctx.invoke(navigate, folderid=destination)
