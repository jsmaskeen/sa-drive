# SA Drive (Service Account Drive)


## Why is it needed ?
Since now team drives or shared drives (whichever you may prefer) are not available for free using `td.msgsuite.workers.dev` or any such generators.

Even if they are available, they are limited to 100GiB.

This project aims to give a displayable + managable look to the drive storage of service accounts.

## How it works ?
Each service account has a 15GiB of drive storage. 
If you have a 100 service accounts [i.e. use only 1 google cloud project], then you have roughly 1.46 TiB of storage

When you upload files using the web interface, ![](https://i.imgur.com/x40pzu2.png) the program automatically detects a service account with enough storage to upload the file, and uploads it to that service account's google drive.

Hence in this way you can exceed the 15GiB storage of your personal drive.

## Limitations
You cannot upload a file whoose size exceeds 15 GiB (Specifically `15784004812 Bytes` or about `14.69GiB`)

## Best Case Scenario
Each Gmail account can create 12 projects. i.e. 12*100 service accounts. 
Hence you can effectively get 15\*12\*100 = 18000 GiB of storage, or `roughly 17TiB per gmail account`. With the only limitation being file size of each file about 14.7GiB


## Deployment

1. [OPTIONAL (if you do not have service accounts)] Create service accounts using [AutoRclone](https://github.com/xyou365/AutoRclone) or [Service Account Utility](./Service%20Account%20Utility/) [Video for using Service Account Utility: [Youtube](https://youtu.be/PlR6nXF7WNI)]
2. Download the zip of the repository, extract it and paste the `accounts/` folder in it.
3. Generate a mongodb database uri. [Follow step 1 of this tutorial](https://www.youtube.com/watch?v=MfnP1M0BW7Y)
4. Go to your personal google drive, make a folder there named `sa-drive` or whatever you may like. Keep its folder id handy. Share this folder with the google group where your service accounts are there.
5. Open [_config.py](./_config.py) using any text editor and paste in the folder id [from step 4] in the parent_id variable.
6. Paste the mongodb uri [from step 3] in db_uri variable.
7. Choose a suitable username and password. RENAME IT TO `config.py` . Save and exit.
8. Open command prompt in that folder.
9. [OPTIONAL (but recommended)] Run `pip install virtualenv`. Then run `virtualenv venv`, `cd venv/Scripts`, `activate`, `cd ../..`
10. Run `pip install -r requirements.txt`
11. Run `python main.py`

## Got questions ?

Read [FAQs.](./FAQ.md)

## Video Tutorial

1. Generate service accounts using [Service Account Utility](./Service%20Account%20Utility/) - [Youtube](https://youtu.be/PlR6nXF7WNI)
2. Deploy sa-drive - [Youtube](https://youtu.be/JzlYnIL6azY)
   
## Images
1. You can view the files in Google Drive as well. [Apart from the sa-drive web interface] <br>Google Drive:![](https://i.imgur.com/lUsxy5S.png)<br>Web Interface:![](https://i.imgur.com/0C6rbNZ.png)
2. You can share/star/rename the files/folders with anyone by using the menu accessible by right clicking the item. ![](https://i.imgur.com/m4N5qIn.png)
3. You can see the size occupied by each service account as well. ![](https://i.imgur.com/UK6OhSV.png)

## Note:
1. More features can be requested apart from TODO below by creating an issue.
2. You can send pull requests too. [Please do 🙏]

### TODO
- [x] support uploading an entire folder, with subfolders and files
- [x] drag and grop anywhere to upload
- [ ] view file (with video player if possible)
- [ ] share/unshare selected=> navbar
- [ ] rclone/gclone ul/dl