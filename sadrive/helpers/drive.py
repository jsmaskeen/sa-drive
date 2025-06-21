"""
Provides Google Drive client wrapper using service accounts for authentication.

Includes:
- PatchedDrive subclass for typing
- SADrive class for Drive operations
- Authentication
- File listing, creation, upload, rename, delete
- Sharing/unsharing
- Search and space usage
- Bulk deletion

Constants:
- PARENT_ID: Root folder ID from config
"""
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
import os
from urllib.parse import quote
from sadrive.helpers.utils import get_parent_id, get_accounts_path
from pydrive2.auth import GoogleAuth #type:ignore
from pydrive2.drive import GoogleDrive #type:ignore
from pydrive2.files import GoogleDriveFile #type:ignore
from googleapiclient.http import MediaIoBaseUpload,MediaUploadProgress
from typing import Any, cast, Optional,List
from googleapiclient.discovery import Resource
from io import IOBase


PARENT_ID = get_parent_id()


class PatchedDrive(GoogleDrive):
    """
    Subclass of GoogleDrive with explicit auth attribute for type checking.

    Attributes:
        auth: GoogleAuth instance used for authentication.
    """
    auth: GoogleAuth


class SADrive:
    """
    Service-account-driven Google Drive client.

    Uses pydrive2 and googleapiclient to perform common operations.
    """
    def __init__(self, service_account_num: str) -> None:
        """
        Initializes the SADrive client.

        Args:
            service_account_num: Index of the service account to use (as string).
        """
        self.sa_num = int(service_account_num)
        self.cwd = os.getcwd()
        self.drive: PatchedDrive = self.authorise()
        self._service = cast(Resource, self.drive.auth.service)

    def list_files(self, parent_id: str = "root"):
        """
        Lists non-trashed files under a given folder.

        Args:
            parent_id: Drive folder ID (default: 'root').

        Returns:
            List of GoogleDriveFile instances.
        """
        files: List[GoogleDriveFile] = cast(
            List[GoogleDriveFile],
            self.drive.ListFile(
                {"q": f"'{parent_id}' in parents and trashed=false"}
            ).GetList(),
        )
        return files

    def create_folder(self, subfolder_name: str, parent_folder_id: str = "root") -> str:
        """
        Creates a new folder in Drive.

        Args:
            subfolder_name: Name for the new folder.
            parent_folder_id: ID of the parent folder (default 'root').

        Returns:
            The ID of the created folder.
        """
        newFolder = self.drive.CreateFile(
                {
                    "title": subfolder_name,
                    "parents": [{"id": parent_folder_id}],
                    "mimeType": "application/vnd.google-apps.folder",
                }
            )
        
        newFolder.Upload()
        newFolder.FetchMetadata(fetch_all=True)
        return cast(str, newFolder.get("id", ""))

    def upload_file(self, filename: str, parent_folder_id: str, stream_bytes: IOBase):
        """
        Uploads a file stream to Drive with resumable media.

        Args:
            filename: Name to assign in Drive.
            parent_folder_id: ID of the destination folder.
            stream_bytes: File-like object providing binary data.

        Yields:
            Progress percentage integers until upload completes.

        Returns:
            The upload response dict from the Drive API.
        """
        # media = MediaFileUpload('pig.png', mimetype='image/png', resumable=True)
        media = MediaIoBaseUpload(
            fd=stream_bytes,
            mimetype="application/octet-stream",
            resumable=True,
            chunksize=100 * 1024 * 1024,
        )
        request = cast(
            Any,
            self._service.files().insert(
                media_body=media,
                body={"title": filename, "parents": [{"id": parent_folder_id}]},
                supportsAllDrives=True,
            ),
        )
        media.stream()
        response: Optional[dict[str, Any]] = None
        while response is None:
            status: Optional[MediaUploadProgress]
            status, response = request.next_chunk()
            if status:
                yield int(status.progress() * 100)
        return response

        # response {'kind': 'drive#file', 'userPermission': {'id': 'me', 'type': 'user', 'role': 'owner', 'kind': 'drive#permission', 'selfLink': 'https://www.googleapis.com/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/permissions/me', 'etag': '"A-u9H6ZnEvMXyM640YFpek6R0yk"', 'pendingOwner': False}, 'fileExtension': '', 'md5Checksum': '8e323c60b37c3a6a890b24b9ba68ac4f', 'selfLink': 'https://www.googleapis.com/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr', 'ownerNames': ['mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com'], 'lastModifyingUserName': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'editable': True, 'writersCanShare': True, 'downloadUrl': 'https://www.googleapis.comhttps:/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr?alt=media&source=downloadUrl', 'mimeType': 'application/octet-stream', 'parents': [{'selfLink': 'https://www.googleapis.com/drive/v2/files/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/parents/1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC', 'id': '1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC', 'isRoot': False, 'kind': 'drive#parentReference', 'parentLink': 'https://www.googleapis.com/drive/v2/files/1at0dM_hN2GFVn8ANGOlFwvo5ZcJy38XC'}], 'appDataContents': False, 'iconLink': 'https://drive-thirdparty.googleusercontent.com/16/type/application/octet-stream', 'shared': True, 'lastModifyingUser': {'displayName': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'kind': 'drive#user', 'isAuthenticatedUser': True, 'permissionId': '14036184373008939997', 'emailAddress': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'picture': {'url': 'https://lh3.googleusercontent.com/a/default-user=s64'}}, 'owners': [{'displayName': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'kind': 'drive#user', 'isAuthenticatedUser': True, 'permissionId': '14036184373008939997', 'emailAddress': 'mfc-s4z3no6lohxf2hzaw-vz76v-k3@fight-club-377114.iam.gserviceaccount.com', 'picture': {'url': 'https://lh3.googleusercontent.com/a/default-user=s64'}}], 'headRevisionId': '0ByzOS1ESBxMOK0h4T0pUSWF4Nmw1OWp0azJweVFNL3JQdk1vPQ', 'copyable': True, 'etag': '"MTY4OTY3NzMzOTEwNw"', 'alternateLink': 'https://drive.google.com/file/d/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/view?usp=drivesdk', 'embedLink': 'https://drive.google.com/file/d/1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr/preview?usp=drivesdk', 'webContentLink': 'https://drive.google.com/uc?id=1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr&export=download', 'fileSize': '543572585', 'copyRequiresWriterPermission': False, 'spaces': ['drive'], 'id': '1Wfr9scVNpIE5tBNAg7LKproAWbinqpwr', 'title': 'Untitled', 'labels': {'viewed': True, 'restricted': False, 'starred': False, 'hidden': False, 'trashed': False}, 'explicitlyTrashed': False, 'createdDate': '2023-07-18T10:48:59.107Z', 'modifiedDate': '2023-07-18T10:48:59.107Z', 'modifiedByMeDate': '2023-07-18T10:48:59.107Z', 'lastViewedByMeDate': '2023-07-18T10:48:59.107Z', 'markedViewedByMeDate': '1970-01-01T00:00:00.000Z', 'quotaBytesUsed': '543572585', 'version': '1', 'originalFilename': 'Untitled', 'capabilities': {'canEdit': True, 'canCopy': True}}

    def rename(self, fileid: str, new_name: str):
        """
        Renames an existing Drive file.

        Args:
            fileid: ID of the file to rename.
            new_name: New title for the file.

        Returns:
            The updated GoogleDriveFile instance.
        """
        f = self.drive.CreateFile({"id": fileid})
        f["title"] = new_name
        f.Upload()
        return f

    def share(self, fileid: str):
        """
        Publishes a file by granting 'reader' permission to anyone.

        Args:
            fileid: ID of the file to share.

        Returns:
            The file's alternateLink.
        """
        f = self.drive.CreateFile({"id": fileid})
        f.InsertPermission({"type": "anyone", "value": "anyone", "role": "reader"})
        return cast(str, f["alternateLink"])

    def authorise(self) -> PatchedDrive:
        """
        Authenticates using a service account JSON.

        Uses pydrive2.GoogleAuth with service backend settings.

        Returns:
            An authenticated PatchedDrive instance.
        """
        settings: dict[str, Any] = {
            "client_config_backend": "service",
            "service_config": {
                "client_json_file_path": f"{get_accounts_path()}\\{self.sa_num}.json",
            },
        }
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)
        return cast(PatchedDrive, drive)

    def delete_file(self, file_id: str):
        """
        Deletes a file in Drive.

        Args:
            file_id: ID of the file to remove.
        """
        f = self.drive.CreateFile({"id": file_id})
        f.Delete()

    def unshare(self, file_id: str):
        """
        Revokes 'anyone' permission from a file.

        Args:
            file_id: ID of the file to unshare.
        """
        f =  self.drive.CreateFile({"id": file_id})
        f.DeletePermission("anyone")

    def search(self, name: str):
        """
        Searches for files whose titles contain a substring.

        Args:
            name: Substring to match in file titles.

        Returns:
            List of dict representations of matched files.
        """
        l = cast(
            List[GoogleDriveFile],
            self.drive.ListFile(
                {"q": f"(title contains '{quote(name,safe='')}') and trashed=false"}
            ).GetList(),
        )
        files = cast(List[dict[str, Any]], [dict(i) for i in l])
        return files

    def used_space(self):
        """
        Retrieves the total bytes used by the authenticated account.

        Returns:
            Bytes used as an integer.
        """
        about = cast(dict[Any, Any], self.drive.GetAbout())
        return int(about["quotaBytesUsed"])

    def delete_all_files(self):
        """
        Permanently deletes all non-trashed files owned by the account.

        Iterates pages of up to 1000 items, printing progress to stdout.
        """
        drive=self.drive
        query = "'me' in owners and trashed=false"
        page_token = None

        while True:
            params = { #type:ignore
                'q': query,
                'maxResults': 1000,
                'supportsAllDrives': True,
                'includeItemsFromAllDrives': True,
            }
            if page_token:
                params['pageToken'] = page_token

            file_list = cast(List[GoogleDriveFile], drive.ListFile(params).GetList())
            if not file_list:
                break

            for f in file_list:
                name = f.get('name', f.get('title')) #type:ignore
                fid = f['id'] #type:ignore
                try:
                    print(f"Deleting file: {name} (ID: {fid})")
                    f.Delete()
                except Exception as e:
                    print(f"  → Failed to delete {name}: {e}")

            page_token = getattr(file_list, 'nextPageToken', None)
            if not page_token:
                print("Finished deleting all owned files.")
                break
    

