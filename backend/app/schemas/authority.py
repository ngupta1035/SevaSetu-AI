from pydantic import BaseModel, Field

from app.models.enums import IssueStatus


class AssignIn(BaseModel):
    department_id: int | None = None          # default: the department the router chose
    notes: str | None = Field(default=None, max_length=500)   # e.g. assignee / work order


class StatusIn(BaseModel):
    status: IssueStatus
    comment: str | None = Field(default=None, max_length=500)


class VerifyIn(BaseModel):
    approved: bool
    comment: str | None = Field(default=None, max_length=500)
