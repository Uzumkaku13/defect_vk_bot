from __future__ import annotations

import mimetypes
from pathlib import Path

import requests

VK_API_VERSION = "5.199"


def upload_doc_to_vk(token: str, peer_id: int, file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(file_path)

    server_resp = requests.get(
        "https://api.vk.com/method/docs.getMessagesUploadServer",
        params={
            "type": "doc",
            "peer_id": peer_id,
            "access_token": token,
            "v": VK_API_VERSION,
        },
        timeout=60,
    ).json()

    if "error" in server_resp:
        raise RuntimeError(f"VK docs.getMessagesUploadServer: {server_resp['error']}")

    upload_url = server_resp["response"]["upload_url"]
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    with path.open("rb") as f:
        upload_resp = requests.post(
            upload_url,
            files={"file": (path.name, f, content_type)},
            timeout=120,
        ).json()

    if "file" not in upload_resp:
        raise RuntimeError(f"Ошибка загрузки файла в VK: {upload_resp}")

    save_resp = requests.get(
        "https://api.vk.com/method/docs.save",
        params={
            "file": upload_resp["file"],
            "title": path.name,
            "access_token": token,
            "v": VK_API_VERSION,
        },
        timeout=60,
    ).json()

    if "error" in save_resp:
        raise RuntimeError(f"VK docs.save: {save_resp['error']}")

    doc = save_resp["response"]["doc"]
    return f"doc{doc['owner_id']}_{doc['id']}"
