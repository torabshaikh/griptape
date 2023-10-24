from __future__ import annotations
import logging
from typing import List, Dict, Any
from schema import Schema, Literal, Optional, Or
from attr import define, field
from griptape.artifacts import (
    ErrorArtifact,
    InfoArtifact,
    ListArtifact,
    BlobArtifact,
    TextArtifact,
)
from griptape.utils.decorators import activity
from griptape.tools import BaseGoogleClient
from io import BytesIO


@define
class GoogleDriveClient(BaseGoogleClient):
    LIST_FILES_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    UPLOAD_FILE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

    GOOGLE_EXPORT_MIME_MAPPING = {
        "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    DEFAULT_FOLDER_PATH = "root"

    SERVICE_NAME = "drive"

    SERVICE_VERSION = "v3"

    owner_email: str = field(kw_only=True)

    @activity(
        config={
            "description": "Can be used to list files in a specific Google Drive folder.",
            "schema": Schema(
                {
                    Optional(
                        "folder_path",
                        default=DEFAULT_FOLDER_PATH,
                        description="Path of the Google Drive folder (like 'MainFolder/Subfolder1/Subfolder2') "
                        "from which files should be listed.",
                    ): str
                }
            ),
        }
    )
    def list_files(self, params: dict) -> ListArtifact | ErrorArtifact:
        values = params["values"]
        from google.auth.exceptions import MalformedError

        folder_path = values.get("folder_path", self.DEFAULT_FOLDER_PATH)

        try:
            service = self._build_client(
                self.LIST_FILES_SCOPES,
                self.SERVICE_NAME,
                self.SERVICE_VERSION,
                self.owner_email,
            )

            if folder_path == self.DEFAULT_FOLDER_PATH:
                query = "mimeType != 'application/vnd.google-apps.folder' and 'root' in parents and trashed=false"
            else:
                folder_id = self._convert_path_to_file_id(service, folder_path)
                if folder_id:
                    query = f"'{folder_id}' in parents and trashed=false"
                else:
                    return ErrorArtifact(
                        f"Could not find folder: {folder_path}"
                    )

            items = self._list_files(service, query)
            return ListArtifact([TextArtifact(i) for i in items])

        except MalformedError:
            return ErrorArtifact(
                "error listing files due to malformed credentials"
            )
        except Exception as e:
            return ErrorArtifact(f"error listing files from Google Drive: {e}")

    @activity(
        config={
            "description": "Can be used to save memory artifacts to Google Drive using folder paths",
            "schema": Schema(
                {
                    "memory_name": str,
                    "artifact_namespace": str,
                    "file_name": str,
                    Optional(
                        "folder_path",
                        description="Path of the Google Drive folder (like 'MainFolder/Subfolder1/Subfolder2') "
                        "where the file should be saved.",
                        default=DEFAULT_FOLDER_PATH,
                    ): str,
                }
            ),
        }
    )
    def save_memory_artifacts_to_drive(
        self, params: dict
    ) -> ErrorArtifact | InfoArtifact:
        values = params["values"]
        memory = self.find_input_memory(values["memory_name"])
        file_name = values["file_name"]
        folder_path = values.get("folder_path", self.DEFAULT_FOLDER_PATH)

        if memory:
            artifacts = memory.load_artifacts(values["artifact_namespace"])

            if artifacts:
                service = self._build_client(
                    self.UPLOAD_FILE_SCOPES,
                    self.SERVICE_NAME,
                    self.SERVICE_VERSION,
                    self.owner_email,
                )

                if folder_path == self.DEFAULT_FOLDER_PATH:
                    folder_id = self.DEFAULT_FOLDER_PATH
                else:
                    folder_id = self._convert_path_to_file_id(
                        service, folder_path
                    )

                if folder_id:
                    try:
                        if len(artifacts) == 1:
                            self._save_to_drive(
                                file_name, artifacts[0].value, folder_id
                            )
                        else:
                            for a in artifacts:
                                self._save_to_drive(
                                    f"{a.name}-{file_name}", a.value, folder_id
                                )

                        return InfoArtifact(f"saved successfully")

                    except Exception as e:
                        return ErrorArtifact(
                            f"error saving file to Google Drive: {e}"
                        )
                else:
                    return ErrorArtifact(
                        f"Could not find folder: {folder_path}"
                    )
            else:
                return ErrorArtifact("no artifacts found")
        else:
            return ErrorArtifact("memory not found")

    @activity(
        config={
            "description": "Can be used to save content to a file on Google Drive",
            "schema": Schema(
                {
                    Literal(
                        "path",
                        description="Destination file path on Google Drive in the POSIX format. "
                        "For example, 'foo/bar/baz.txt'",
                    ): str,
                    "content": str,
                }
            ),
        }
    )
    def save_content_to_drive(
        self, params: dict
    ) -> ErrorArtifact | InfoArtifact:
        content = params["values"]["content"]
        filename = params["values"]["path"]

        try:
            self._save_to_drive(filename, content)

            return InfoArtifact(f"saved successfully")
        except Exception as e:
            return ErrorArtifact(f"error saving file to Google Drive: {e}")

    @activity(
        config={
            "description": "Can be used to download multiple files from Google Drive based on a provided list of paths",
            "schema": Schema(
                {
                    Literal(
                        "paths",
                        description="List of paths to files to be loaded in the POSIX format. "
                        "For example, ['foo/bar/file1.txt', 'foo/bar/file2.txt']",
                    ): [str]
                }
            ),
        }
    )
    def download_files(self, params: dict) -> ListArtifact | ErrorArtifact:
        from google.auth.exceptions import MalformedError
        from googleapiclient.errors import HttpError

        values = params["values"]
        downloaded_files = []

        try:
            service = self._build_client(
                self.LIST_FILES_SCOPES,
                self.SERVICE_NAME,
                self.SERVICE_VERSION,
                self.owner_email,
            )

            for path in values["paths"]:
                file_id = self._convert_path_to_file_id(service, path)
                if file_id:
                    file_info = service.files().get(fileId=file_id).execute()
                    mime_type = file_info["mimeType"]

                    if mime_type in self.GOOGLE_EXPORT_MIME_MAPPING:
                        export_mime = self.GOOGLE_EXPORT_MIME_MAPPING[mime_type]
                        request = service.files().export_media(
                            fileId=file_id, mimeType=export_mime
                        )
                    else:
                        request = service.files().get_media(fileId=file_id)

                    downloaded_files.append(BlobArtifact(request.execute()))
                else:
                    logging.error(f"Could not find file: {path}")

            return ListArtifact(downloaded_files)
        except HttpError as e:
            return ErrorArtifact(f"error downloading file in Google Drive: {e}")
        except MalformedError:
            return ErrorArtifact(
                "error downloading file due to malformed credentials"
            )
        except Exception as e:
            return ErrorArtifact(f"error downloading file to Google Drive: {e}")

    @activity(
        config={
            "description": "Can search for files on Google Drive based on name or content",
            "schema": Schema(
                {
                    Literal(
                        "search_mode",
                        description="File search mode. Use 'name' to search in file name or "
                        "'content' to search in file content",
                    ): Or("name", "content"),
                    Literal(
                        "search_query",
                        description="Query to search for. If search_mode is 'name', it's the file name. If 'content', "
                        "it's the text within files.",
                    ): str,
                    Optional(
                        "folder_path",
                        description="Path of the Google Drive folder (like 'MainFolder/Subfolder1/Subfolder2') "
                        "where the search should be performed.",
                        default=DEFAULT_FOLDER_PATH,
                    ): str,
                }
            ),
        }
    )
    def search_files(self, params: dict) -> ListArtifact | ErrorArtifact:
        from google.auth.exceptions import MalformedError
        from googleapiclient.errors import HttpError

        values = params["values"]

        search_mode = values["search_mode"]
        folder_path = values.get("folder_path", self.DEFAULT_FOLDER_PATH)

        try:
            service = self._build_client(
                self.LIST_FILES_SCOPES,
                self.SERVICE_NAME,
                self.SERVICE_VERSION,
                self.owner_email,
            )

            folder_id = None
            if folder_path == self.DEFAULT_FOLDER_PATH:
                folder_id = self.DEFAULT_FOLDER_PATH
            else:
                folder_id = self._convert_path_to_file_id(service, folder_path)

            if folder_id:
                query = None
                if search_mode == "name":
                    query = f"name='{values['search_query']}'"
                elif search_mode == "content":
                    query = f"fullText contains '{values['search_query']}'"

                query += " and trashed=false"
                if folder_id != self.DEFAULT_FOLDER_PATH:
                    query += f" and '{folder_id}' in parents"

                results = service.files().list(q=query).execute()
                items = results.get("files", [])
                return ListArtifact([TextArtifact(i) for i in items])
            else:
                return ErrorArtifact(f"Folder path {folder_path} not found")

        except HttpError as e:
            return ErrorArtifact(
                f"error searching for file in Google Drive: {e}"
            )
        except MalformedError:
            return ErrorArtifact(
                "error searching for file due to malformed credentials"
            )
        except Exception as e:
            return ErrorArtifact(f"error searching file to Google Drive: {e}")

    def _save_to_drive(
        self, filename: str, value: any, parent_folder_id=None
    ) -> InfoArtifact | ErrorArtifact:
        from googleapiclient.http import MediaIoBaseUpload

        service = self._build_client(
            self.UPLOAD_FILE_SCOPES,
            self.SERVICE_NAME,
            self.SERVICE_VERSION,
            self.owner_email,
        )

        if isinstance(value, str):
            value = value.encode()

        parts = filename.split("/")
        if len(parts) > 1:
            directory = "/".join(parts[:-1])
            parent_folder_id = self._convert_path_to_file_id(service, directory)
            if not parent_folder_id:
                return ErrorArtifact(f"Could not find folder: {directory}")
            filename = parts[-1]

        file_metadata = {"name": filename}
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        media = MediaIoBaseUpload(
            BytesIO(value), mimetype="application/octet-stream", resumable=True
        )

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return InfoArtifact(file)

    def _list_files(self, service: Any, query: str) -> List[Dict]:
        items = []
        next_page_token = None

        while True:
            results = (
                service.files()
                .list(q=query, pageToken=next_page_token)
                .execute()
            )

            files = results.get("files", [])
            items.extend(files)

            next_page_token = results.get("nextPageToken")
            if not next_page_token:
                break

        return items
