from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.domain.models import Message, SessionState


class FirebaseStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.db = None
        self.local_dir = Path(self.settings.local_data_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self._init_firestore()

    def _init_firestore(self) -> None:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if firebase_admin._apps:
                self.db = firestore.client()
                return

            cred = None
            if self.settings.firebase_credentials_path:
                cred = credentials.Certificate(self.settings.firebase_credentials_path)
            elif self.settings.firebase_service_account_json:
                data = json.loads(self.settings.firebase_service_account_json)
                cred = credentials.Certificate(data)

            if cred:
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
            elif not self.settings.use_local_store_if_firebase_missing:
                raise RuntimeError("Missing Firebase credentials")
        except Exception:
            if not self.settings.use_local_store_if_firebase_missing:
                raise
            self.db = None

    def _session_file(self, session_id: str) -> Path:
        return self.local_dir / f"{session_id}.json"

    async def create_session(self, session: SessionState) -> None:
        if self.db:
            self.db.collection("sessions").document(session.session_id).set(session.model_dump())
            return
        self._write_local(session, [])

    async def get_session(self, session_id: str) -> SessionState | None:
        if self.db:
            doc = self.db.collection("sessions").document(session_id).get()
            if not doc.exists:
                return None
            return SessionState(**doc.to_dict())
        path = self._session_file(session_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**data["session"])

    async def update_session(self, session: SessionState) -> None:
        if self.db:
            self.db.collection("sessions").document(session.session_id).set(session.model_dump(), merge=True)
            return
        messages = await self.get_messages(session.session_id, limit=9999)
        self._write_local(session, messages)

    async def add_message(self, message: Message) -> None:
        if self.db:
            self.db.collection("sessions").document(message.session_id).collection("messages").document(message.message_id).set(message.model_dump())
            return
        session = await self.get_session(message.session_id)
        messages = await self.get_messages(message.session_id, limit=9999)
        messages.append(message)
        if session:
            self._write_local(session, messages)

    async def get_messages(self, session_id: str, limit: int = 20) -> list[Message]:
        if self.db:
            docs = (
                self.db.collection("sessions")
                .document(session_id)
                .collection("messages")
                .order_by("created_at")
                .stream()
            )
            messages = [Message(**doc.to_dict()) for doc in docs]
            return messages[-limit:]
        path = self._session_file(session_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        messages = [Message(**m) for m in data.get("messages", [])]
        return messages[-limit:]

    def _write_local(self, session: SessionState, messages: list[Message]) -> None:
        payload: dict[str, Any] = {
            "session": session.model_dump(),
            "messages": [m.model_dump() for m in messages],
        }
        self._session_file(session.session_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    async def list_sessions(self, user_id: str, limit: int = 20,) -> list[SessionState]:
        if self.db:
            docs = (
                self.db.collection("sessions")
                .where("user_id", "==", user_id)
                .order_by("updated_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            sessions = [SessionState(**doc.to_dict()) for doc in docs]
            return sessions

        files = sorted(
            self.local_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        sessions: list[SessionState] = []

        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                session = SessionState(**data["session"])

                if session.user_id != user_id:
                    continue

                sessions.append(session)

                if len(sessions) >= limit:
                    break
            except Exception:
                continue

        return sessions
    async def delete_session(self, session_id: str) -> None:
        if self.db:
            session_ref = self.db.collection("sessions").document(session_id)

            messages = session_ref.collection("messages").stream()

            for msg in messages:
                msg.reference.delete()

            session_ref.delete()
            return

        path = self._session_file(session_id)

        if path.exists():
            path.unlink()