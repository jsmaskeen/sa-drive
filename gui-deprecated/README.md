
## Deployment

1. Generate a mongodb database uri. [Follow step 1 of this tutorial](https://www.youtube.com/watch?v=MfnP1M0BW7Y)
2. Go to your personal google drive, make a folder there named `sa-drive` or whatever you may like. Keep its folder id handy. Share this folder with the google group where your service accounts are there.
3. Open [_config.py](./_config.py) using any text editor and paste in the folder id [from step 4] in the parent_id variable.
4. Paste the mongodb uri [from step 1] in db_uri variable.
5. Choose a suitable username and password. RENAME IT TO `config.py` . Save and exit.
6. Open command prompt in that folder.
7. [OPTIONAL (but recommended)] Run `pip install virtualenv`. Then run `virtualenv venv`, `cd venv/Scripts`, `activate`, `cd ../..`
8. Run `pip install -r requirements.txt`
9. Run `python main.py`

## Video Tutorial
Deploy sa-drive - [Youtube](https://youtu.be/JzlYnIL6azY)

## Images
1. You can view the files in Google Drive as well. [Apart from the sa-drive web interface] <br>Google Drive:![](https://i.ibb.co/5x4BF8cy/image.png)<br>Web Interface:![](https://i.ibb.co/SDzTwmty/image.png)
2. You can share/star/rename the files/folders with anyone by using the menu accessible by right clicking the item. ![](https://i.ibb.co/6Rm1xNS0/image.png)
3. You can see the size occupied by each service account as well. ![](https://i.imgur.com/UK6OhSV.png)