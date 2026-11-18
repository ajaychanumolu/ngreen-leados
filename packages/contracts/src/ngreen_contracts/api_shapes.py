"""Shared API shapes. These are contracts, not implemented routes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ApiErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)
    request_id: str | None = None


class Page[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
