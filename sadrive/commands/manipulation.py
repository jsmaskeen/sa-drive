"""
Provides CLI commands for common SA-Drive operations:
- newfolder: Create a new Drive folder and record it locally.
- share: Share files or folders (recursive) and update DB.
- rename: Rename a Drive item and update DB.
- open_link: Open a Drive item in the browser.
- details: Display storage usage table for all service accounts.
- search: Interactive search of files/folders by name.
"""
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import click
from sadrive.helpers.utils import (
    get_parent_id,
    humanbytes,
    MAGIC_SIZE,
    FF
)
import webbrowser
from sadrive.helpers.drive import SADrive
import sadrive.helpers.dbf as dbf
from click import Context
from prettytable import PrettyTable
from typing import cast
import inquirer #type:ignore


@click.command()
@click.argument("name")
@click.argument("destination", default=get_parent_id())
def newfolder(name: str, destination: str):
    """
    Create a folder in SA-Drive at the given destination ID.

    Args:
        name: Name of the new folder to create.
        destination: Drive folder ID under which to create (default: root).

    Side Effects:
        - Calls Drive API to create the folder.
        - Inserts the folder record into local DB.
        - Prints the new folder ID.
    """
    fd = dbf.get_file_details(destination)
    if destination != get_parent_id():
        if (not fd) or fd["type"] == "file":
            click.echo("Destination folder id does not exist !!")
            return
    drive = SADrive('0')
    f = drive.create_folder(name,destination)
    dbf.insert_file(f,name,destination,0,'folder','0',False)
    click.echo(f"Folder created, folderid = {f}")
    

def share_file_base(sa_num:str,file_id:str):
    """
    Share a single file by granting reader permission to anyone.

    Args:
        sa_num: Service account number as string.
        file_id: Drive file or folder ID.

    Returns:
        Shareable link for the item.
    """
    drive = SADrive(sa_num)
    link = drive.share(file_id)
    dbf.share_file(file_id,True)
    return link


def share_folder_recursive(file_id:str):
    """
    Recursively mark all items inside a folder as shared.

    Args:
        file_id: ID of the parent folder.
    """
    children = dbf.find_children(file_id)
    for child in children:
        if child['type'] == 'file':
            dbf.share_file(child['_id'],True)
        elif child['type'] == 'folder':
            share_folder_recursive(child['_id'])
    dbf.share_file(file_id,True)

@click.command()
@click.argument("id", default=get_parent_id())
def share(id: str):
    """
    Share a file or folder (recursive) with anyone.

    Args:
        id: Drive item ID to share (default: root).

    Side Effects:
        - Updates sharing permissions via Drive API.
        - Updates local DB share flags.
        - Prints the shareable link.
    """
    fd = dbf.get_file_details(id)
    if (not fd):
        click.echo("Destination id does not exist !!")
        return
    if fd['type'] == 'folder':
        share_folder_recursive(fd['_id'])

    link = share_file_base(fd['service_acc_num'],fd['_id'])
    click.echo(f"Shared Link (anyone can view) = {link}")
    

@click.command()
@click.argument("newname")
@click.argument("id")
def rename(newname: str,id:str):
    """
    Rename a Drive file or folder.

    Args:
        newname: New name for the item.
        id: Drive item ID to rename.

    Side Effects:
        - Calls Drive API to rename.
        - Updates local DB record.
    """
    fd = dbf.get_file_details(id)
    if (not fd):
        click.echo("Destination id does not exist !!")
        return
    sa_num = fd['service_acc_num']
    drive = SADrive(sa_num)
    drive.rename(id,newname)
    dbf.rename_file(id,newname)

@click.command()
@click.argument('id')
def open_link(id:str):
    """
    Open the given file or folder ID in the default web browser.

    Args:
        id: Drive item ID.

    Side Effects:
        - Launches browser to the Drive open URL.
    """
    webbrowser.open(f'https://drive.google.com/open?id={id}')
    click.echo(f"Opened https://drive.google.com/open?id={id}")
    
@click.command()
def details():
    """
    Display storage usage details for all service accounts.

    Prints a table with occupied and free space per account.
    """
    items =[(i['_id'],i['size']) for i in dbf.get_size_map()]
    items.sort(key=lambda x:x[1],reverse=True)
    occ,avail = dbf.space_details()
    click.echo(f"Space details are as follows:\nOccupied:{humanbytes(occ)} | Available: {humanbytes(avail)}")
    table = PrettyTable()
    table.field_names = ["SA number", "Occupied", "Free"]
    for num,sz in items:
        table.add_row([num,humanbytes(sz),humanbytes(MAGIC_SIZE-sz)])
    click.echo(table.get_string())
    return   


def search_for_file(file_name:str,fuzzy:bool):
    """
    Search for files by name, either via Drive API fuzzy search or DB substring matching.

    Args:
        file_name: The search term to match filenames against.
        fuzzy: If True, perform fuzzy search through Drive API; else, use database LIKE search.

    Returns:
        List of file detail dicts matching the search criteria.

    Behavior:
        - Fuzzy: Retrieves Drive files via SADrive.search, then filters those present in the DB.
        - Non-fuzzy: Directly queries DB for filenames containing the term.
    """
    if fuzzy:
        actual = []
        hp = SADrive('0')
        ls = hp.search(file_name)
        for i in ls:
            tmp  = dbf.get_file_details(i['id'])
            if tmp:
                actual.append(tmp)
    else:
        actual = dbf.search_for_file_contains(file_name)
    return actual

@click.command()
@click.argument('name')
@click.argument('fuzzy',default=True)
@click.pass_context
def search(ctx:Context,name:str,fuzzy:bool):
    """
    Search the SA-Drive for files or folders by name.

    Args:
        name: Substring to search for.
        fuzzy: If True, use Drive API fuzzy search; else database LIKE search.

    Side Effects:
        - Prompts user to select a result interactively.
        - Opens the selected item in browser via `open_link`.
    """
    data = search_for_file(name,fuzzy)
    choices = [
            FF(i["file_name"], i["_id"], i["parent_id"], i["type"])
            for i in data
        ]
    choices.append(FF('exit','','',''))
    answer = cast(dict[str,FF],inquirer.prompt(
            [
                inquirer.List(
                    "choice", message=f"Search results for {name} and {fuzzy=}. Press enter on a choice to open in browser!", choices=choices
                )
            ]
        ))
    choice = answer["choice"]
    if choice.name == 'exit':
        return
    ctx.invoke(open_link,id=choice.file_id)
    
