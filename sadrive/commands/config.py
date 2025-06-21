"""
Commands:

- set_dir(path): Set and persist the config directory.
- show(): Display the currently configured directory.

This module uses `click` to create a user-friendly interface.
"""

import click
from pathlib import Path
from sadrive.helpers.utils import CONFIG_POINTER,get_config_dir

@click.group()
def config():
    """
    Top-level configuration command group.

    Use this group to manage application settings,
    such as the config directory location.
    """
    pass

@config.command()
@click.argument("path")
def set_dir(path:str):
    """
    Sets and remembers the configuration directory.

    Args:
        path: Filesystem path to use as the config directory. 
              Will be created if it does not exist.

    Side Effects:
        - Creates the directory (including parents) if missing.
        - Writes the resolved path to CONFIG_POINTER file.
        - Prints a confirmation message.
    """
    config_path = Path(path).expanduser().resolve()
    config_path.mkdir(parents=True, exist_ok=True)
    CONFIG_POINTER.write_text(str(config_path))
    click.echo(f"Config directory set to {config_path}")
    
@config.command()
def show():
    """
    Shows the currently configured directory.

    Prints:
        The path previously set by `set_dir`.

    Raises:
        RuntimeError: If no config directory has been set.
    """
    click.echo(get_config_dir())
