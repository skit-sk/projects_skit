import httpx
import logging
import asyncio
import mimetypes
from pathlib import Path
from config import MAX_BOT_TOKEN, MAX_WEBHOOK_SECRET

log = logging.getLogger("max_bot")

BASE_URL = "https://platform-api.max.ru"

class MAXClient:
    def __init__(self, token: str = MAX_BOT_TOKEN):
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": token},
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=0),
        )

    async def close(self):
        await self.client.aclose()

    async def get_me(self) -> dict:
        r = await self.client.get("/me")
        r.raise_for_status()
        return r.json()

    async def send_message(
        self,
        user_id: int,
        text: str,
        format: str | None = None,
        keyboard: list | None = None,
        chat_id: int | None = None,
        notify: bool = True,
    ) -> dict | None:
        if not text and not keyboard:
            return None
        body: dict = {}
        if text:
            body["text"] = text[:4000]
        if format:
            body["format"] = format
        if keyboard:
            body["attachments"] = [
                {"type": "inline_keyboard", "payload": {"buttons": keyboard}}
            ]
        if notify is False:
            body["notify"] = False

        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id

        try:
            r = await self.client.post("/messages", params=params, json=body)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"send_message failed (uid={user_id}): {e}")
            return None

    async def edit_message(
        self, chat_id: int, message_id: str, text: str, format: str | None = None
    ) -> dict | None:
        body: dict = {}
        if text:
            body["text"] = text[:4000]
        if format:
            body["format"] = format
        try:
            r = await self.client.put(f"/messages/{message_id}", json=body)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"edit_message failed (mid={message_id}): {e}")
            return None

    async def delete_message(self, message_id: str) -> bool:
        try:
            r = await self.client.delete(f"/messages/{message_id}")
            r.raise_for_status()
            return True
        except Exception as e:
            log.error(f"delete_message failed (mid={message_id}): {e}")
            return False

    async def upload_file(self, file_type: str, file_path: str | Path) -> str | None:
        type_map = {
            "image": "image",
            "video": "video",
            "audio": "audio",
            "file": "file",
        }
        ft = type_map.get(file_type, "file")
        try:
            r1 = await self.client.post("/uploads", params={"type": ft})
            r1.raise_for_status()
            upload_url = r1.json()["url"]
        except Exception as e:
            log.error(f"upload get_url failed: {e}")
            return None

        try:
            with open(file_path, "rb") as f:
                r2 = await self.client.post(
                    upload_url,
                    files={"data": (Path(file_path).name, f, mimetypes.guess_type(str(file_path))[0] or "application/octet-stream")},
                )
            r2.raise_for_status()
            result = r2.json()
            if ft == "image":
                token = None
                for photo_data in result.get("photos", {}).values():
                    token = photo_data.get("token")
                    if token:
                        break
                if not token:
                    token = result.get("token")
            elif ft in ("video", "audio"):
                token = result.get("token")
            else:
                token = result.get("token")
            if not token and "url" in result:
                token = result["url"].split("?token=")[-1] if "?token=" in result["url"] else result["url"]
            return token
        except Exception as e:
            log.error(f"upload file failed ({file_path}): {e}")
            return None

    async def send_image(
        self,
        user_id: int,
        image_path: str | Path,
        caption: str | None = None,
        chat_id: int | None = None,
    ) -> dict | None:
        token = await self.upload_file("image", image_path)
        if not token:
            log.error(f"send_image: upload returned no token for {image_path}")
            return None
        log.info(f"send_image: uploaded {image_path}, waiting for processing...")
        await asyncio.sleep(3)
        body: dict = {
            "attachments": [{"type": "image", "payload": {"token": token}}]
        }
        if caption:
            body["text"] = caption[:4000]
        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id
        try:
            r = await self.client.post("/messages", params=params, json=body)
            r.raise_for_status()
            log.info(f"send_image: sent to uid={user_id}")
            return r.json()
        except Exception as e:
            log.error(f"send_image failed (uid={user_id}): {e}")
            return None

    async def send_file(
        self,
        user_id: int,
        file_path: str | Path,
        caption: str | None = None,
        chat_id: int | None = None,
    ) -> dict | None:
        token = await self.upload_file("file", file_path)
        if not token:
            log.error(f"send_file: upload returned no token for {file_path}")
            return None
        log.info(f"send_file: uploaded {file_path}, waiting...")
        await asyncio.sleep(3)
        body: dict = {
            "attachments": [{"type": "file", "payload": {"token": token}}]
        }
        if caption:
            body["text"] = caption[:4000]
        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        else:
            params["user_id"] = user_id
        try:
            r = await self.client.post("/messages", params=params, json=body)
            r.raise_for_status()
            log.info(f"send_file: sent to uid={user_id}")
            return r.json()
        except Exception as e:
            err_body = getattr(e, 'response', None)
            if err_body is not None:
                try:
                    err_body = err_body.text[:300]
                except Exception:
                    pass
            log.error(f"send_file failed (uid={user_id}): {e} body={err_body}")
            return None

    async def answer_callback(self, callback_id: str, text: str | None = None) -> bool:
        body: dict = {}
        if text:
            body["text"] = text[:4000]
        try:
            r = await self.client.post(f"/answers?callback_id={callback_id}", json=body)
            r.raise_for_status()
            return True
        except Exception as e:
            log.error(f"answer_callback failed ({callback_id}): {e}")
            return False

    async def get_message(self, message_id: str) -> dict | None:
        try:
            r = await self.client.get(f"/messages/{message_id}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"get_message failed (mid={message_id}): {e}")
            return None

    async def get_messages(self, user_id: int | None = None, chat_id: int | None = None, limit: int = 50) -> list:
        params = {"limit": limit}
        if chat_id:
            params["chat_id"] = chat_id
        elif user_id:
            params["user_id"] = user_id
        try:
            r = await self.client.get("/messages", params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("messages", [])
        except Exception as e:
            log.error(f"get_messages failed: {e}")
            return []

    async def setup_webhook(
        self, url: str, secret: str | None = None, update_types: list[str] | None = None
    ) -> dict:
        body: dict = {"url": url}
        if secret:
            body["secret"] = secret
        if update_types:
            body["update_types"] = update_types
        try:
            r = await self.client.post("/subscriptions", json=body)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"setup_webhook failed: {e}")
            return {"success": False, "message": str(e)}

    async def delete_webhook(self) -> dict:
        try:
            r = await self.client.delete("/subscriptions")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"delete_webhook failed: {e}")
            return {"success": False, "message": str(e)}

    async def get_updates(
        self,
        marker: int | None = None,
        timeout: int = 30,
        limit: int = 100,
        types: list[str] | None = None,
    ) -> dict:
        params = {"timeout": timeout, "limit": limit}
        if marker is not None:
            params["marker"] = marker
        if types:
            params["types"] = types
        try:
            r = await self.client.get("/updates", params=params)
            r.raise_for_status()
            return r.json()
        except httpx.TimeoutException:
            return {"updates": [], "marker": marker}
        except Exception as e:
            log.error(f"get_updates failed: {e}")
            return {"updates": [], "marker": marker}

    async def get_chat_info(self, chat_id: int) -> dict | None:
        try:
            r = await self.client.get(f"/chats/{chat_id}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.error(f"get_chat_info failed (cid={chat_id}): {e}")
            return None
