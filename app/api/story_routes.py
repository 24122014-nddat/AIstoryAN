from __future__ import annotations

from fastapi import APIRouter, HTTPException, Header, Depends

from app.domain.schemas import (
    SessionResponse,
    StartGameRequest,
    StoryResponse,
    TurnRequest,
    NovelStartRequest,
    NovelWorldResponse,
    NovelFoundationRequest,
)
from app.services.story_service import StoryService
from app.config import get_settings
from app.auth.firebase_auth import get_current_user

router = APIRouter(prefix="/game", tags=["Story"])
service = StoryService()


@router.post("/start", response_model=StoryResponse)
async def start_game(
    request: StartGameRequest,
    user=Depends(get_current_user),
):
    try:
        return await service.start_game(request, user_id=user["uid"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/turn", response_model=StoryResponse)
async def continue_story(
    request: TurnRequest,
    user=Depends(get_current_user),
):
    try:
        return await service.continue_story(request, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions")
async def list_sessions(
    user=Depends(get_current_user),
):
    try:
        return await service.list_sessions(user_id=user["uid"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user=Depends(get_current_user),
):
    try:
        return await service.delete_session(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user=Depends(get_current_user),
):
    try:
        session, messages = await service.get_session(session_id, user_id=user["uid"])
        return SessionResponse(
            session=session,
            messages=messages,
            gold=session.gold,
            inventory=session.inventory,
            party=session.party,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{session_id}/admin/memory")
async def admin_memory(
    session_id: str,
    x_admin_token: str | None = Header(default=None),
):
    settings = get_settings()

    if not settings.admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        return await service.debug_memory(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
@router.post("/novel/world", response_model=NovelWorldResponse)
async def start_novel_world(
    request: NovelStartRequest,
    user=Depends(get_current_user),
):
    try:
        return await service.start_novel_world(
            request,
            user_id=user["uid"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/novel/foundation", response_model=StoryResponse)
async def create_novel_foundation(
    request: NovelFoundationRequest,
    user=Depends(get_current_user),
):
    try:
        return await service.create_novel_foundation(
            request,
            user_id=user["uid"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc