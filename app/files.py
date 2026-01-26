"""File handling utilities for Salesforce ContentDocument and ContentVersion objects."""

import base64
import mimetypes
import re
from typing import Optional
from urllib.parse import urljoin

from simple_salesforce import Salesforce
from simple_salesforce.format import format_soql

# Regex pattern for validating Salesforce IDs (15 or 18 alphanumeric characters)
SALESFORCE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{15}(?:[a-zA-Z0-9]{3})?$")

# Mapping of Salesforce FileType to MIME types
SALESFORCE_FILETYPE_TO_MIME = {
    "PDF": "application/pdf",
    "WORD": "application/msword",
    "WORD_X": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "EXCEL": "application/vnd.ms-excel",
    "EXCEL_X": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "POWER_POINT": "application/vnd.ms-powerpoint",
    "POWER_POINT_X": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "PNG": "image/png",
    "JPG": "image/jpeg",
    "JPEG": "image/jpeg",
    "GIF": "image/gif",
    "BMP": "image/bmp",
    "TIFF": "image/tiff",
    "SVG": "image/svg+xml",
    "TEXT": "text/plain",
    "CSV": "text/csv",
    "XML": "application/xml",
    "JSON": "application/json",
    "ZIP": "application/zip",
    "MP3": "audio/mpeg",
    "MP4": "video/mp4",
    "MOV": "video/quicktime",
    "AVI": "video/x-msvideo",
}


def validate_salesforce_id(sf_id: str) -> str:
    """Validate a Salesforce ID format.

    Args:
        sf_id: The Salesforce ID to validate

    Returns:
        The validated and trimmed ID

    Raises:
        ValueError: If the ID is not a string or format is invalid
    """
    if not isinstance(sf_id, str):
        raise ValueError(f"Salesforce ID must be a string, got {type(sf_id).__name__}")
    sf_id = sf_id.strip()
    if not SALESFORCE_ID_PATTERN.match(sf_id):
        raise ValueError(f"Invalid Salesforce ID format: {sf_id}")
    return sf_id


def get_mime_type(file_type: Optional[str], file_extension: Optional[str]) -> str:
    """Get MIME type from Salesforce FileType or file extension.

    Args:
        file_type: Salesforce FileType value (e.g., "PDF", "WORD_X")
        file_extension: File extension with or without leading dot (e.g., "pdf", ".pdf")

    Returns:
        MIME type string, defaults to "application/octet-stream" if unknown
    """
    if file_type and file_type.upper() in SALESFORCE_FILETYPE_TO_MIME:
        return SALESFORCE_FILETYPE_TO_MIME[file_type.upper()]

    if file_extension:
        # Ensure extension has leading dot for mimetypes.guess_type
        ext = file_extension if file_extension.startswith(".") else f".{file_extension}"
        mime_type, _ = mimetypes.guess_type(f"file{ext}")
        if mime_type:
            return mime_type

    return "application/octet-stream"


def get_latest_version_id(sf: Salesforce, document_id: str) -> str:
    """Get the latest ContentVersion ID for a ContentDocument.

    Args:
        sf: Authenticated Salesforce client
        document_id: The ContentDocument ID

    Returns:
        The ContentVersion ID of the latest version

    Raises:
        ValueError: If the ID format is invalid or document is not found
        SalesforceError: If API call fails (permissions, malformed request, etc.)
    """
    validate_salesforce_id(document_id)

    result = sf.query(
        format_soql(
            "SELECT LatestPublishedVersionId FROM ContentDocument WHERE Id = {}",
            document_id,
        )
    )

    if not result["records"]:
        raise ValueError(f"ContentDocument not found: {document_id}")

    return result["records"][0]["LatestPublishedVersionId"]


def get_version_metadata(sf: Salesforce, version_id: str) -> dict:
    """Get metadata for a ContentVersion.

    Args:
        sf: Authenticated Salesforce client
        version_id: The ContentVersion ID

    Returns:
        Dictionary with version metadata

    Raises:
        ValueError: If the ID format is invalid or version is not found
        SalesforceError: If API call fails (permissions, malformed request, etc.)
    """
    validate_salesforce_id(version_id)

    result = sf.query(
        format_soql(
            """SELECT Id, ContentDocumentId, Title, PathOnClient, FileType,
                FileExtension, ContentSize, VersionNumber, IsLatest,
                CreatedDate, LastModifiedDate, Description
            FROM ContentVersion
            WHERE Id = {}""",
            version_id,
        )
    )

    if not result["records"]:
        raise ValueError(f"ContentVersion not found: {version_id}")

    record = result["records"][0]
    return {
        "id": record["Id"],
        "document_id": record["ContentDocumentId"],
        "title": record["Title"],
        "filename": record.get("PathOnClient"),
        "file_type": record.get("FileType"),
        "file_extension": record.get("FileExtension"),
        "size": record.get("ContentSize"),
        "version_number": record.get("VersionNumber"),
        "is_latest": record.get("IsLatest"),
        "created_date": record.get("CreatedDate"),
        "last_modified_date": record.get("LastModifiedDate"),
        "description": record.get("Description"),
        "mime_type": get_mime_type(record.get("FileType"), record.get("PathOnClient")),
    }


def get_document_metadata(sf: Salesforce, document_id: str) -> dict:
    """Get metadata for a ContentDocument including all versions.

    Args:
        sf: Authenticated Salesforce client
        document_id: The ContentDocument ID

    Returns:
        Dictionary with document metadata and versions

    Raises:
        ValueError: If the ID format is invalid or document is not found
        SalesforceError: If API call fails (permissions, malformed request, etc.)
    """
    validate_salesforce_id(document_id)

    doc_result = sf.query(
        format_soql(
            """SELECT Id, Title, FileType, FileExtension, ContentSize,
                LatestPublishedVersionId, CreatedDate, LastModifiedDate,
                OwnerId, Description
            FROM ContentDocument
            WHERE Id = {}""",
            document_id,
        )
    )

    if not doc_result["records"]:
        raise ValueError(f"ContentDocument not found: {document_id}")

    doc = doc_result["records"][0]

    versions_result = sf.query(
        format_soql(
            """SELECT Id, VersionNumber, ContentSize, CreatedDate, PathOnClient
            FROM ContentVersion
            WHERE ContentDocumentId = {}
            ORDER BY CreatedDate DESC""",
            document_id,
        )
    )

    versions = [
        {
            "id": v["Id"],
            "version_number": v.get("VersionNumber"),
            "size": v.get("ContentSize"),
            "filename": v.get("PathOnClient"),
            "created_date": v.get("CreatedDate"),
            "resource_uri": f"salesforce://file/{document_id}/version/{v['Id']}",
        }
        for v in versions_result["records"]
    ]

    return {
        "id": doc["Id"],
        "title": doc.get("Title"),
        "file_type": doc.get("FileType"),
        "file_extension": doc.get("FileExtension"),
        "size": doc.get("ContentSize"),
        "latest_version_id": doc.get("LatestPublishedVersionId"),
        "created_date": doc.get("CreatedDate"),
        "last_modified_date": doc.get("LastModifiedDate"),
        "owner_id": doc.get("OwnerId"),
        "description": doc.get("Description"),
        "mime_type": get_mime_type(doc.get("FileType"), doc.get("FileExtension")),
        "resource_uri": f"salesforce://file/{doc['Id']}",
        "versions": versions,
    }


def download_file_content(sf: Salesforce, version_id: str) -> bytes:
    """Download binary content from a ContentVersion.

    Args:
        sf: Authenticated Salesforce client
        version_id: The ContentVersion ID

    Returns:
        Binary file content

    Raises:
        ValueError: If the ID format is invalid

    Note:
        Uses simple_salesforce's internal _call_salesforce method as there is
        no public API for blob downloads. This is the standard approach per
        https://github.com/simple-salesforce/simple-salesforce/issues/704
    """
    validate_salesforce_id(version_id)

    # Ensure proper URL construction regardless of whether base_url has trailing slash
    base = sf.base_url if sf.base_url.endswith("/") else sf.base_url + "/"
    url = urljoin(base, f"sobjects/ContentVersion/{version_id}/VersionData")
    response = sf._call_salesforce("GET", url)
    return response.content


def download_file_content_base64(sf: Salesforce, version_id: str) -> str:
    """Download file content and return as base64-encoded string.

    Args:
        sf: Authenticated Salesforce client
        version_id: The ContentVersion ID

    Returns:
        Base64-encoded file content

    Raises:
        ValueError: If the ID format is invalid
    """
    content = download_file_content(sf, version_id)
    return base64.b64encode(content).decode("utf-8")


def search_content_documents(
    sf: Salesforce,
    query: str,
    file_extension: Optional[str] = None,
    linked_record_id: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """Search ContentDocuments by title with optional filters.

    Args:
        sf: Authenticated Salesforce client
        query: Search term to match against file titles
        file_extension: Optional file extension filter (e.g., 'pdf', 'docx')
        linked_record_id: Optional record ID to filter by linked entity
        limit: Maximum number of results (1-200)

    Returns:
        List of matching file metadata dictionaries

    Raises:
        ValueError: If linked_record_id is provided but invalid
    """
    # Validate and sanitize limit
    if not isinstance(limit, int):
        raise TypeError(f"limit must be an int, got {type(limit).__name__}")
    limit = max(1, min(200, limit))

    if linked_record_id:
        validate_salesforce_id(linked_record_id)

        # Build query with format_soql for safe parameterization
        # Always select the same fields for consistent output
        if file_extension:
            soql = format_soql(
                """SELECT ContentDocument.Id, ContentDocument.Title,
                    ContentDocument.FileType, ContentDocument.FileExtension,
                    ContentDocument.ContentSize, ContentDocument.LatestPublishedVersionId
                FROM ContentDocumentLink
                WHERE LinkedEntityId = {}
                AND ContentDocument.Title LIKE '%{:like}%'
                AND ContentDocument.FileExtension = {}
                LIMIT {:literal}""",
                linked_record_id,
                query,
                file_extension.lower(),
                str(limit),
            )
        else:
            soql = format_soql(
                """SELECT ContentDocument.Id, ContentDocument.Title,
                    ContentDocument.FileType, ContentDocument.FileExtension,
                    ContentDocument.ContentSize, ContentDocument.LatestPublishedVersionId
                FROM ContentDocumentLink
                WHERE LinkedEntityId = {}
                AND ContentDocument.Title LIKE '%{:like}%'
                LIMIT {:literal}""",
                linked_record_id,
                query,
                str(limit),
            )

        result = sf.query(soql)

        files = []
        for record in result["records"]:
            doc = record["ContentDocument"]
            files.append(
                {
                    "id": doc["Id"],
                    "title": doc.get("Title"),
                    "file_type": doc.get("FileType"),
                    "file_extension": doc.get("FileExtension"),
                    "size": doc.get("ContentSize"),
                    "latest_version_id": doc.get("LatestPublishedVersionId"),
                    "mime_type": get_mime_type(
                        doc.get("FileType"), doc.get("FileExtension")
                    ),
                    "resource_uri": f"salesforce://file/{doc['Id']}",
                }
            )
        return files
    else:
        # Build query with format_soql for safe parameterization
        if file_extension:
            soql = format_soql(
                """SELECT Id, Title, FileType, FileExtension,
                    ContentSize, LatestPublishedVersionId
                FROM ContentDocument
                WHERE Title LIKE '%{:like}%'
                AND FileExtension = {}
                LIMIT {:literal}""",
                query,
                file_extension.lower(),
                str(limit),
            )
        else:
            soql = format_soql(
                """SELECT Id, Title, FileType, FileExtension,
                    ContentSize, LatestPublishedVersionId
                FROM ContentDocument
                WHERE Title LIKE '%{:like}%'
                LIMIT {:literal}""",
                query,
                str(limit),
            )

        result = sf.query(soql)

        return [
            {
                "id": doc["Id"],
                "title": doc.get("Title"),
                "file_type": doc.get("FileType"),
                "file_extension": doc.get("FileExtension"),
                "size": doc.get("ContentSize"),
                "latest_version_id": doc.get("LatestPublishedVersionId"),
                "mime_type": get_mime_type(
                    doc.get("FileType"), doc.get("FileExtension")
                ),
                "resource_uri": f"salesforce://file/{doc['Id']}",
            }
            for doc in result["records"]
        ]


def get_files_for_record(sf: Salesforce, record_id: str) -> list[dict]:
    """Get all files linked to a Salesforce record via ContentDocumentLink.

    Args:
        sf: Authenticated Salesforce client
        record_id: The Salesforce record ID (Account, Opportunity, etc.)

    Returns:
        List of file metadata dictionaries

    Raises:
        ValueError: If the record ID format is invalid
    """
    validate_salesforce_id(record_id)

    # Use format_soql for safe parameterization
    result = sf.query(
        format_soql(
            """SELECT ContentDocumentId, ContentDocument.Title,
                ContentDocument.FileType, ContentDocument.FileExtension,
                ContentDocument.ContentSize, ContentDocument.LatestPublishedVersionId,
                ContentDocument.CreatedDate, ContentDocument.LastModifiedDate
            FROM ContentDocumentLink
            WHERE LinkedEntityId = {}""",
            record_id,
        )
    )

    return [
        {
            "id": record["ContentDocumentId"],
            "title": record["ContentDocument"].get("Title"),
            "file_type": record["ContentDocument"].get("FileType"),
            "file_extension": record["ContentDocument"].get("FileExtension"),
            "size": record["ContentDocument"].get("ContentSize"),
            "latest_version_id": record["ContentDocument"].get(
                "LatestPublishedVersionId"
            ),
            "created_date": record["ContentDocument"].get("CreatedDate"),
            "last_modified_date": record["ContentDocument"].get("LastModifiedDate"),
            "mime_type": get_mime_type(
                record["ContentDocument"].get("FileType"),
                record["ContentDocument"].get("FileExtension"),
            ),
            "resource_uri": f"salesforce://file/{record['ContentDocumentId']}",
        }
        for record in result["records"]
    ]
