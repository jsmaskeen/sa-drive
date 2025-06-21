"""
sadrive CLI Entrypoint

Main command-line interface for the SA-Drive application, managing cloud storage
uploads, downloads, navigation, and service account configuration using Google Drive.

Commands are modularly registered from submodules and grouped into the `sadrive` command.

Behavior:
    - On every invocation (except `config set-dir`), validates that a config directory
      has been set and initializes the rclone config if missing.
    - Delegates to subcommands such as upload, navigate, search, delete, share, etc.

Subcommands:
    - config: Configure SA-Drive environment (set or show config path)
    - update_sas: Synchronize service account usage with DB
    - upload: Upload a file or directory to SA-Drive
    - navigate: Browse remote Drive structure
    - mount: Mount SA-Drive using gclone
    - delete: Delete a specific file or folder from Drive and DB
    - clearall: Wipe all Drive contents across accounts
    - newfolder: Create a folder in SA-Drive
    - download: Download a file or folder using gclone
    - rebuild: Reconstruct a .sapart split file
    - share: Share a file/folder via link
    - rename: Rename a file/folder on Drive
    - open-link: Open a file/folder in browser
    - search: Fuzzy or strict search for files
    - details: Show storage usage by each service account

Usage:
    sadrive <subcommand> [options]

Example:
    sadrive upload ~/Videos/movie.mp4
"""
import click
import sys
from sadrive.helpers.utils import get_config_dir,set_rclone_conf

@click.group()
@click.pass_context
def sadrive(ctx:click.Context):
    invoked = ctx.invoked_subcommand
    if invoked != "config" or (ctx.args and ctx.args[0] != "set-dir"):
        try:
            get_config_dir()
            set_rclone_conf()
        except RuntimeError as e:
            click.echo(str(e), err=True)
            sys.exit(1)
        
from sadrive.commands.config import config
sadrive.add_command(config, name='config')
try:
    from sadrive.commands.upload import upload
    sadrive.add_command(upload, name='upload')

    from sadrive.commands.navigate import navigate,mount
    sadrive.add_command(navigate, name='navigate')
    sadrive.add_command(mount, name='mount')

    from sadrive.commands.delete import delete,clearall
    sadrive.add_command(delete, name='delete')
    sadrive.add_command(clearall, name='clearall')

    from sadrive.commands.downlaod import rebuild,download
    sadrive.add_command(download, name='download')
    sadrive.add_command(rebuild, name='rebuild')

    from sadrive.commands.manipulation import newfolder,share,rename,open_link,details,search
    sadrive.add_command(newfolder, name='newfolder')
    sadrive.add_command(search, name='search')
    sadrive.add_command(share, name='share')
    sadrive.add_command(rename, name='rename')
    sadrive.add_command(open_link, name='open-link')
    sadrive.add_command(details, name='details')
    sadrive.add_command(details, name='details')

    from sadrive.commands.db import update_sas
    sadrive.add_command(update_sas, name='update_sas')
except Exception as e:
    print(e)

if __name__ == "__main__":
    sadrive()
