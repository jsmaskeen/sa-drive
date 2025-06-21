"""
Defines the `update_sas` CLI command to synchronize service account
storage usage with the local database.

This command:
- Scans the local service accounts directory for JSON credentials.
- Ensures any new accounts are added to the database.
- Fetches actual used storage for each account via the Drive API.
- Updates the database sizes accordingly (sync mode).

Uses a ThreadPoolExecutor for concurrent API calls.
"""
import click
from sadrive.helpers.utils import get_accounts_path
from sadrive.helpers.drive import SADrive
import os
from concurrent.futures import ThreadPoolExecutor,as_completed
import sadrive.helpers.dbf as dbf
from typing import Any


@click.command()
def update_sas():
    """
    Synchronize service account usage with the database.

    Scans the local accounts directory and the database to find any
    service accounts not yet recorded and adds them with zero usage.
    Then, for all accounts in the database, concurrently fetches the
    actual used storage from Google Drive and updates the size map in
    sync mode (overwriting previous values).

    Side Effects:
        - Inserts missing service accounts into `sa_size_map` via `dbf.insert_size_map`.
        - Updates each service account's `size` field to the Drive API value via `dbf.add_size(syncing=True)`.
        - Prints status messages to stdout and echoes completion via Click.
    """
    sas_on_local = {int(i.split('.')[0]) for i in os.listdir(get_accounts_path())}
    sas_on_db = {int(i['_id']) for i in dbf.get_size_map()}
    sas_not_on_db = sas_on_local - sas_on_db
    if len(sas_not_on_db) !=0:
        print(f'Following SA\'s were not on db: {sas_not_on_db}. Adding them.....')
        for i in sas_not_on_db:
            dbf.insert_size_map(str(i),0)
            
    def process_size_map_entry(i:dict[Any,Any]):
        sa_num = i['_id']
        used_storage = SADrive(sa_num).used_space()
        dbf.add_size(sa_num, used_storage, True)
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(process_size_map_entry, i) for i in dbf.get_size_map()]
        for future in as_completed(futures):
            future.result()
    click.echo("Updated Service accounts on db with actual size!")

        
    
