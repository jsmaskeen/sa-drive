"""
Provides CLI commands for deleting files and folders from Google Drive
and updating the local database accordingly. Supports recursive folder deletion
and full cleanup of all service-account drives.

Functions:
- del_file: Remove a single file from Drive and database.
- del_folder: Recursively delete a folder and its contents.

Commands:
- delete(fileid): Delete a specific file or folder by ID.
- clearall(): Wipe all files across all service accounts and reset DB.
"""

# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import click
from sadrive.helpers.drive import SADrive
import sadrive.helpers.dbf as dbf
from concurrent.futures import ThreadPoolExecutor, as_completed


def del_file(sa_num:str,file_id:str):
    """
    Deletes a single file from Google Drive and removes its record from the DB.

    Args:
        sa_num: Service account number owning the file.
        file_id: Drive file ID to delete.
    """
    drive = SADrive(str(sa_num))
    drive.delete_file(file_id)
    dbf.delete_file(file_id)
    
def del_folder(sa_num:str,file_id:str):
    """
    Recursively deletes all contents of a folder in Drive and the database,
    then deletes the folder itself.

    Args:
        sa_num: Service account number owning the folder.
        file_id: Drive folder ID to delete.
    """
    children = dbf.find_children(file_id)
    for child in children:
        if child['type'] == 'file':
            del_file(child['service_acc_num'],child['_id'])
        elif child['type'] == 'folder':
            del_folder(child['service_acc_num'],child['_id'])
    del_file(sa_num,file_id)

@click.command()
@click.argument("fileid")
def delete(fileid: str):
    """
    CLI command to delete a file or folder by its ID.

    If the ID corresponds to a folder, deletion is recursive.

    Args:
        fileid: The Drive ID of the file or folder.

    Side Effects:
        - Removes the file/folder from Google Drive.
        - Updates the local database to reflect deletion.
        - Prints status messages to the console.
    """
    fd = dbf.get_file_details(fileid)
    if (not fd):
        click.echo("Destination folder/file id does not exist !!")
        return
    if fd["type"] == "file":
        del_file(fd['service_acc_num'],fileid)
    else:
        del_folder(fd['service_acc_num'],fileid)
        
@click.command()
def clearall():
    """
    CLI command to permanently delete all files across all service accounts
    and reset the local file and size maps.

    Side Effects:
        - Deletes every non-trashed file owned by each service account.
        - Clears the file_map table.
        - Resets all service account sizes to zero.
        - Prints progress and a final confirmation message.
    """
    drives = [SADrive(i['_id']) for i in dbf.get_size_map()]
    def delete_all(drive:SADrive):
        drive.delete_all_files()
        return
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(delete_all, d) for d in drives]
        for future in as_completed(futures):
            future.result()
    dbf.clear_file_map()
    dbf.reset_sa_sizes()
    click.echo("SA Drive has been reset.")
            