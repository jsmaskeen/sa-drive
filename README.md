# SA Drive (Service Account Drive)

## Note: As of April 15 2025, New service accounts will not have 15GiB of Google Drive Storage, hence this repository is specifically targeted at those users who have service accounts generated before April 15 2025, and wish to combine their storage into a unified place. 

### Note to old users (who used GUI version): This repository was previously aimed at the GUI version, see [gui-deprecated](./gui-deprecated/), which was maintained by another author. Now the live workings are supported by the [cli](./sadrive/). Which is much more powerful than the GUI, it shows progress, has support to mount the sa-drive with gclone onto local filesystem, and most importantly, supports large file upload ( > 14.7 GiB). [BONUS: The CLI is implemented in a statically typed way using type hints.]

## Why is it needed ?
Now Team Drives or shared drives (whichever you may prefer) are have a restriction of ~100GiB. So, to circumvent that, 
using Google's own services, this project aims to give a displayable + managable look to the drive storage of service accounts.

## How it works ?
Each service account has a 15GiB of drive storage. 
If you have a 100 service accounts [i.e. use only 1 google cloud project], then you have roughly 1.46 TiB of storage

When you upload files using the cli, the program automatically detects a service account with enough storage to upload the file, and uploads it to that service account's google drive.

Hence in this way you can exceed the 15GiB storage of your personal drive.
## Features:
- Mount the drive as a local filesystem.
- Simultaneous uploads.
- Simultaneous downloads (using gclone).
- Split large files (>14.7 GiB).
- Progress bars, ETA etc.
- Fuzzy Search.

## Deployment
1. Do `pip install sadrive`
2. Make a folder named `config_dir` or whatever at your choice of location.
3. Make sure that config dir has a folder with the name accounts, which contains the json representation of service accounts. Also it should have a config.json file with the following content:
    ```json
    {
    "parent_id": "1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC", // ID of google drive fodler in your personal account where you want the sa-drive to be hosted.
    "path_to_gclone.exe":"C:\\Users\\HEMAN\\Desktop\\\\gclone-l3v11\\gclone.exe" // Path to gclone.exe. Downlaod from: https://github.com/l3v11/gclone
    }
    ```
    The `config_dir` should look like this:
    ![](https://i.ibb.co/VW4dpV43/image.png)
3. Run the command `sadrive config set-dir absolute/path/to/config_dir`. 
4. Now you are done. Just use any of the commands. 
4. Visit [https://sadrive.readthedocs.io/en/latest/](https://sadrive.readthedocs.io/en/latest/). For detailed documentation, and examples.

## Images and Examples
1. `sadrive`
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image.png)
2. `sadrive config set-dir <path>` 
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-1.png)
3. `sadrive rename newname file/folderid`
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-2.png)
4. `sadrive navigate [optional_folderid]`
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-3.png)
5. `sadrive share file/folderid`
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-4.png)
6. `sadrive mount` [This gives a read only filesystem, you can directly view/open files from this]
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-5.png)
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-6.png)
7. `sadrive delete file/folderid`
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-7.png)
8. `sadrive newfolder name [optional_destination_id]`
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-8.png)
9. `sadrive upload path/to/upload destination_folder_id` If destination folder id is not provided then it will upload to the parent directory set in `config.json`.
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-9.png)
10. `sadrive download folder_id path/to/destination [--transfers int]`. transfers represents the maximum number of parallel downloads you want.
    ![alt text](https://raw.githubusercontent.com/jsmaskeen/sa-drive/refs/heads/main/docs/_static/images/image-10.png)

## Limitations
None as of now.

## Best Case Scenario
Each Gmail account can create 12 projects. i.e. 12*100 service accounts. 
Hence you can effectively get 15\*12\*100 = 18000 GiB of storage, or `roughly 17TiB per gmail account`.

## Got questions ?

Read [FAQs.](./FAQ.md)