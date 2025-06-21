# FAQs

### Note:
sa-drive uses service accounts and utilise the Google Cloud Console, and Google APIs.
Abuse of this feature is not the aim of sa-drive and we do NOT recommend that you make a lot of projects, just one project and 100 sa will give you 1.4TB of storage which is sufficient.

## What programs do I need to install prior to setting up sa-drive?
Only one, Python. Get it from [Python.org](https://python.org/)
## Is it safe to use sa-drive? Would this get my account banned?
Yes It is safe to use sa-drive.<br>No it would not get your account banned. But if you host any copyrighted content the google might take the content down.
<br>
Its also possible that overabuse os the Service Accounts might get your cloud-projects banned by google.

## What is a service account?
This is best answered by [google itself](https://cloud.google.com/iam/docs/service-account-overview)

## Can I use sa-drive with a VPN?

Ideally you should but you might get ssl errors when creating service accounts using [Service Account Utility](./Service%20Account%20Utility/) or when running the sa-drive, the database might give ssl errors.
<br>
Hence it is recommened to switch off the vpn.

## Should I use my alternate Gmail account for this, or would my personal Gmail account also suffice?

Again, if you do not abuse the service accounts feature then your personal gmail would be fine. But I'd still recommend a alternate Gmail account which dyou do not use for any personal or official business.

## Do I have to name my folder/group in a specific format?

No you are free to choose the root folder (parent folder) name as well as the google group name.

## Do I really need to have exactly 100 service accounts? Can't I have less or more?

You can have any number of service accounts you want. 100 is given because when adding the service account emails to the google group, a user has the limit of adding 100 members (or emails) per day.

## Would tweaking with the Cloud Console this much have any effect on the Gmail account?

Not at all. Google Could Console is meant to be used by the users, to make their lives easier lol.

## Do I need to be logged in my browser with the required account in order to use sa-drive?

Nope. You can log out from the gmail account and still use the sa-drive. 

## Is any personal information being shared about my account to others?

Nope. Everything is built by the user after all. Your information is within your hands (and google's ofcourse)

## What if I add the group to two folders at once?

Not an issue. Because sa-drive will consider only that folder as the parent folder which you add in the [_config.py](./_config.py). [Don't forget to rename the file to config.py]

## Would sa-drive use up existing leftover storage space from my account?

Not at all. The sa-drive utilises the drive space of each service account, and doesn't handle anything in your personal drive

## What if I need to expand the storage further?

1. Simply make another project in google cloud console
2. then enable just the google drive api and iam service management api in that project.
3. no need to create consent screen , credentials or all that stuff
4. then run the service account utitlity with the previous credentials [which you would have got when you'd have made the service accounts for the first time.]
5. while choosing the project to create service accounts in, choose the newly created projectId in step 1.
6. Add the emails of those new service accounts to the google group
7. rename the account files in increasing order. Like if you already have 0-99 .json, rename the new ones from 100-199 .json.
8. Copy those 100-199 .json files and paste it into the accounts folder.

Thats all.

## Why don't my starred files show up when I open Google Drive?

That is because the files are not actually being starred in Google Drive. The starred files are visible in the sa-drive ui only.

I can make the files to be starred in google drive, but that would require additional setting up to do. 
Kindly make an issue on github if you wish to have this feature.

## What does SA index indicate?
SA index indicates the filename of the service account.json file in the accounts folder.

## What if I want to change the account with which I access `sa-drive`?

You cannot. Only option is to disconned the `sa-drive`

## What if I wish to disconnect `sa-drive` from my account?

1. Delete the uploaded files [optional]
2. Delete the service accounts from the project hompage in google cloud console [this should delete the files as well assuming they are not `shared with everyone`]
3. Delete the google could project where your service accounts are made.

## Would I risk corrupting `sa-drive` if I exceed my storage limit?

Nope. The program will automatically give the error of storagequotaexceeded.