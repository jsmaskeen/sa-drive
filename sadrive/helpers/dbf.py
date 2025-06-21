"""
Database operations module for the CLI application.

This module manages SQLite connection, schema initialization, and CRUD operations
for file mappings and service account size tracking.

Provides:
- Connection management
- Table creation for file_map and sa_size_map
- Insert, update, delete, and query functions for file entries
- Service account size tracking and management
- Utility functions for searching and space reporting
"""
import sqlite3
import json
from sadrive.helpers.utils import get_database_path,get_accounts_path,MAGIC_SIZE

def get_connection():
    """
    Opens a SQLite connection to the configured database.

    Returns:
        sqlite3.Connection: Connection object with row_factory set to sqlite3.Row.
    """
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    return conn

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS file_map (
            _id TEXT PRIMARY KEY,
            file_name TEXT,
            parent_id TEXT,
            file_size INTEGER,
            type TEXT,
            service_acc_num TEXT,
            shared INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sa_size_map (
            _id TEXT PRIMARY KEY,
            size INTEGER,
            email TEXT
        )
    ''')
    conn.commit()


def insert_file(
    file_id:str, file_name:str, parent_id:str, file_size:int, type:str, service_acc_num:str, shared:bool
):
    """
    Inserts a new file record into file_map and updates account size.

    Args:
        file_id: Unique identifier of the file in Drive.
        file_name: Name of the file.
        parent_id: Parent folder identifier.
        file_size: Size of the file in bytes.
        type: "file" or "folder".
        service_acc_num: ID of the service account used.
        shared: Whether the file is shared.
    """
    with get_connection() as conn:
        conn.execute(
            '''INSERT INTO file_map
               (_id, file_name, parent_id, file_size, type, service_acc_num, shared)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (file_id, file_name, parent_id, int(file_size), type, service_acc_num, int(shared))
        )
    add_size(service_acc_num, int(file_size))


def clear_file_map():
    """
    Deletes all records from file_map.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM file_map")
        conn.commit()

def reset_sa_sizes():
    """
    Resets all sizes in sa_size_map to zero.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE sa_size_map SET size = 0")
        conn.commit()


def get_file_details(file_id:str):
    """
    Retrieves a file record by its ID.

    Args:
        file_id: Unique identifier to look up.

    Returns:
        dict: File record fields, or None if not found.
    """
    with get_connection() as conn:
        cur = conn.execute('SELECT * FROM file_map WHERE _id = ?', (file_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def rename_file(file_id:str, new_file_name:str):
    """
    Updates the name of a file record.

    Args:
        file_id: ID of the file to rename.
        new_file_name: New name to assign.
    """
    details = get_file_details(file_id)
    if not details:
        return
    with get_connection() as conn:
        conn.execute(
            'UPDATE file_map SET file_name = ? WHERE _id = ?',
            (new_file_name, file_id)
        )
        

def share_file(file_id:str, shared:bool=True):
    """
    Marks a file as shared or unshared.

    Args:
        file_id: ID of the file.
        shared: True to mark shared, False otherwise.
    """
    with get_connection() as conn:
        conn.execute(
            'UPDATE file_map SET shared = ? WHERE _id = ?',
            (int(shared), file_id)
        )


def delete_file(file_id:str):
    """
    Deletes a file record and subtracts its size from the service account.

    Args:
        file_id: ID of the file to remove.
    """
    details = get_file_details(file_id)
    if not details:
        return
    with get_connection() as conn:
        conn.execute('DELETE FROM file_map WHERE _id = ?', (file_id,))
    remove_size(details['service_acc_num'], details['file_size'])

def insert_size_map(sa_num:str, size:int=0):
    """
    Inserts a new entry in sa_size_map with initial size and email from account file.

    Args:
        sa_num: Service account identifier.
        size: Initial size in bytes. Default is 0.
    """
    file_path = f"{get_accounts_path()}\\{sa_num}.json"
    with open(file_path, 'r') as f:
        ce = json.load(f)['client_email']
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO sa_size_map (_id, size, email) VALUES (?, ?, ?)',
            (sa_num, size, ce)
        )


def get_sa_size_taken(sa_num:str):
    """
    Retrieves size and email for a given service account.

    Args:
        sa_num: Service account identifier.

    Returns:
        dict: Record fields, or None if not found.
    """
    with get_connection() as conn:
        cur = conn.execute('SELECT * FROM sa_size_map WHERE _id = ?', (sa_num,))
        row = cur.fetchone()
        return dict(row) if row else None


def add_size(sa_num:str, size:int,syncing:bool=False):
    """
    Updates a service account's size, adding or syncing.

    Args:
        sa_num: ID of the account to update.
        size: Size change in bytes.
        syncing: If True, sets size exactly to 'size'.
    """
    if syncing:
        with get_connection() as conn:
            conn.execute(
                'UPDATE sa_size_map SET size = ? WHERE _id = ?',
                (size, sa_num)
            )
        return
    record = get_sa_size_taken(sa_num)
    if not record:
        insert_size_map(sa_num, size)
        return
    new_size = record['size'] + size
    with get_connection() as conn:
        conn.execute(
            'UPDATE sa_size_map SET size = ? WHERE _id = ?',
            (new_size, sa_num)
        )


def get_size_map():
    """
    Retrieves all service account size records.

    Returns:
        list of dict: Each dict has '_id', 'size', and 'email'.
    """
    with get_connection() as conn:
        cur = conn.execute('SELECT * FROM sa_size_map')
        return [dict(row) for row in cur.fetchall()]


def get_sa_num(email:str):
    """
    Finds a service account ID by its email.

    Args:
        email: Client email to search.

    Returns:
        str or None: Account ID if found.
    """
    with get_connection() as conn:
        cur = conn.execute('SELECT _id FROM sa_size_map WHERE email = ?', (email,))
        row = cur.fetchone()
        return row['_id'] if row else None


def find_children(parent_id:str):
    """
    Lists file_map entries with the given parent_id.

    Args:
        parent_id: Parent folder identifier.

    Returns:
        list of dict: File records under the parent.
    """
    with get_connection() as conn:
        cur = conn.execute('SELECT * FROM file_map WHERE parent_id = ?', (parent_id,))
        return [dict(row) for row in cur.fetchall()]


def remove_size(sa_num:str, size:int):
    """
    Subtracts size from a service account's recorded usage.

    Args:
        sa_num: Account ID.
        size: Bytes to subtract.
    """
    record = get_sa_size_taken(sa_num)
    if not record:
        insert_size_map(sa_num, 0)
        return
    new_size = record['size'] - size
    with get_connection() as conn:
        conn.execute(
            'UPDATE sa_size_map SET size = ? WHERE _id = ?',
            (new_size, sa_num)
        )


def search_for_file_contains(value:str):
    """
    Searches file_map for filenames containing a substring.

    Args:
        value: Substring to search in file_name.

    Returns:
        list of dict: Matching file records.
    """
    pattern = f"%{value}%"
    with get_connection() as conn:
        cur = conn.execute(
            'SELECT * FROM file_map WHERE file_name LIKE ?',
            (pattern,)
        )
        return [dict(row) for row in cur.fetchall()]


def space_details():
    """
    Returns aggregated occupied and available space across accounts.

    Returns:
        occupied (int): Total used bytes.
        available (int): Total available capacity in bytes.
    """
    with get_connection() as conn:
        cur = conn.execute('SELECT size FROM sa_size_map')
        sizes = [row['size'] for row in cur.fetchall()]
    available = MAGIC_SIZE * len(sizes)
    occupied = sum(sizes)
    return occupied, available


def folder_exists(name:str, parent_id:str):
    """
    Checks if a folder entry exists under a parent.

    Args:
        name: Folder name to look for.
        parent_id: Parent folder identifier.

    Returns:
        str or None: Folder ID if exists, else None.
    """
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT _id FROM file_map WHERE parent_id = ? AND file_name = ? AND type = 'folder'",
            (parent_id, name)
        )
        row = cur.fetchone()
        return row['_id'] if row else None
