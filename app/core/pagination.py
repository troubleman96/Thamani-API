from fastapi import Query
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func, Select
from sqlmodel import select
from typing import TypeVar

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Query(default=1, ge=1, description="Page number")
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
) -> tuple[list, PaginationMeta]:
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.exec(count_query)
    total = total_result.one()

    paginated = query.offset(params.offset).limit(params.per_page)
    result = await db.exec(paginated)
    items = result.all()

    pages = (total + params.per_page - 1) // params.per_page

    meta = PaginationMeta(
        total=total,
        page=params.page,
        per_page=params.per_page,
        pages=pages,
        has_next=params.page < pages,
        has_prev=params.page > 1,
    )
    return list(items), meta
