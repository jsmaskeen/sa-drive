
import logging
import os
from urllib.parse import quote
from typing import List


from helpers.utils import humanbytes, list_into_n_parts, humantime
from logutil import logger
import config
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive,GoogleDriveFile
from werkzeug.datastructures import FileStorage
from googleapiclient.http import MediaIoBaseUpload

logging.getLogger("googleapiclient.discovery").setLevel(logging.ERROR)


class SADrive:
    def __init__(self, service_account_num) -> None:
        self.sa_num = int(service_account_num)

        self.cwd = os.getcwd()
        self.drive = self.authorise()
        self._service = self.drive.auth.service

    def list_files(self, parent_id="root"):
        return self.drive.ListFile(
            {"q": f"'{parent_id}' in parents and trashed=false"}
        ).GetList()

    def create_folder(self, subfolder_name, parent_folder_id="root"):
        newFolder = self.drive.CreateFile(
            {
                "title": subfolder_name,
                "parents": [{"id": parent_folder_id}],
                "mimeType": "application/vnd.google-apps.folder",
            }
        )
        newFolder.Upload()
        newFolder.FetchMetadata(fetch_all=True)
        return newFolder.get('id')

    def upload_file_pydrive(self, file: FileStorage, parent_folder_id):
        filename = file.filename
        uploaded = self.drive.CreateFile(
            {"title": filename, "parents": [{"id": parent_folder_id}]}
        )
        uploaded.mimeType = "application/octet-stream"
        uploaded.title = filename
        uploaded.content = file.stream
        uploaded.Upload()
        return uploaded

    def upload_file(self, filename, parent_folder_id,stream_bytes):
        # media = MediaFileUpload('pig.png', mimetype='image/png', resumable=True)
        media = MediaIoBaseUpload(
            fd=stream_bytes, mimetype="application/octet-stream", resumable=True,chunksize=256*1024*1024
        )
        request = self._service.files().insert(
            media_body=media,
            body={"title": filename, "parents": [{"id": parent_folder_id}]},
            supportsAllDrives=True
        )
        media.stream()
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                yield int(status.progress() * 100)
        return response

        # response {'kind': 'drive#file', 'userPermission': {'id': 'me', 'type': 'user', 'role': 'owner', 'kind': 'drive#permission', 'selfLink': 'https://www.googleapis.com/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/permissions/me', 'etag': '"A-u9H6ZnEvMXyM640YFpek6R0yk"', 'pendingOwner': False}, 'fileExtension': '', 'md5Checksum': '8e323c60b37c3a6a890b24b9ba68ac4f', 'selfLink': 'https://www.googleapis.com/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr', 'ownerNames': ['mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com'], 'lastModifyingUserName': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'editable': True, 'writersCanShare': True, 'downloadUrl': 'https://www.googleapis.comhttps:/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr?alt=media&source=downloadUrl', 'mimeType': 'application/octet-stream', 'parents': [{'selfLink': 'https://www.googleapis.com/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/parents/1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC', 'id': '1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC', 'isRoot': False, 'kind': 'drive#parentReference', 'parentLink': 'https://www.googleapis.com/drive/v2/files/1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC'}], 'appDataContents': False, 'iconLink': 'https://drive-thirdparty.googleusercontent.com/16/type/application/octet-stream', 'shared': True, 'lastModifyingUser': {'displayName': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'kind': 'drive#user', 'isAuthenticatedUser': True, 'permissionId': '14036184373008939997', 'emailAddress': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'picture': {'url': 'https://lh3.googleusercontent.com/a/default-user=s64'}}, 'owners': [{'displayName': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'kind': 'drive#user', 'isAuthenticatedUser': True, 'permissionId': '14036184373008939997', 'emailAddress': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'picture': {'url': 'https://lh3.googleusercontent.com/a/default-user=s64'}}], 'headRevisionId': '0ByzOS1ESBxMOK0h4T0pUSWF4Nmw1OWp0azJweVFNL3JQdk1vPQ', 'copyable': True, 'etag': '"MTY4OTY3NzMzOTEwNw"', 'alternateLink': 'https://drive.google.com/file/d/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/view?usp=drivesdk', 'embedLink': 'https://drive.google.com/file/d/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/preview?usp=drivesdk', 'webContentLink': 'https://drive.google.com/uc?id=1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr&export=download', 'fileSize': '543572585', 'copyRequiresWriterPermission': False, 'spaces': ['drive'], 'id': '1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr', 'title': 'Untitled', 'labels': {'viewed': True, 'restricted': False, 'starred': False, 'hidden': False, 'trashed': False}, 'explicitlyTrashed': False, 'createdDate': '2023-07-18T10:48:59.107Z', 'modifiedDate': '2023-07-18T10:48:59.107Z', 'modifiedByMeDate': '2023-07-18T10:48:59.107Z', 'lastViewedByMeDate': '2023-07-18T10:48:59.107Z', 'markedViewedByMeDate': '1970-01-01T00:00:00.000Z', 'quotaBytesUsed': '543572585', 'version': '1', 'originalFilename': 'Untitled', 'capabilities': {'canEdit': True, 'canCopy': True}}

    def rename(self, fileid, new_name):
        f = self.drive.CreateFile({"id": fileid})
        f["title"] = new_name
        f.Upload()
        return f

    def share(self, fileid):
        f = self.drive.CreateFile({"id": fileid})
        f.InsertPermission({"type": "anyone", "value": "anyone", "role": "reader"})
        return f["alternateLink"]

    def authorise(self):
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json_file_path": f"{self.cwd}\\accounts\\{self.sa_num}.json",
            },
        }
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)
        return drive
    
    def delete_file(self,file_id):
        f = self.drive.CreateFile({"id": file_id})
        f.Delete()

    def unshare(self,file_id):
        f = self.drive.CreateFile({"id": file_id})
        f.DeletePermission('anyone')
        

    def search(self,name):
        l:List[GoogleDriveFile] = self.drive.ListFile({'q': f"(title contains '{quote(name,safe='')}') and trashed=false"}).GetList()
        return [dict(i) for i in l]
