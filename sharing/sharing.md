## How to let others view the files you have.

1. Go to Google cloud console, and under some project with drive API enabled, create a service account with read only permissions. 
2. Share the folder you want to share with that service account's email id. And download its keys
3. Then run `sender_script.py path/to/that/service/account folder_or_file_id_to_share`
4. Send the `send_to_receiver.bat` to the user with whom you want to share the file. Make sure user has WinFSP installed ([Link to download](https://winfsp.dev/rel/)).
5. When the user runs the `send_to_receiver.bat`, it automatically downloads gclone, and the viewer service account and mounts it as a filesystem.
 


