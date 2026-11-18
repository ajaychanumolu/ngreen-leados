from fastapi import APIRouter

from ngreen_api.settings import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "auth_mode": settings.auth_mode,
        "database": settings.database_kind,
        "research_mode": "live" if settings.serper_api_key else "demo",
        "worker": settings.research_worker,
        "ai_mode": (
            "live"
            if settings.ai_provider in {"openai", "groq"} and settings.ai_api_key
            else "mock"
        ),
        "voice_mode": (
            "armed"
            if settings.voice_live_enabled
            and settings.voice_legal_approved
            and settings.vapi_api_key
            and settings.vapi_assistant_id
            and settings.vapi_phone_number_id
            and settings.voice_test_contact_id
            else "disabled"
        ),
    }
