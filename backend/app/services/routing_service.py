"""Maps an issue type to the responsible department."""
from sqlalchemy.orm import Session

from app.models import Department
from app.models.enums import IssueType

ISSUE_TO_DEPARTMENT = {
    IssueType.POTHOLE: "Roads",
    IssueType.GARBAGE: "Sanitation",
    IssueType.WATER_LEAKAGE: "Water",
    IssueType.STREETLIGHT: "Electrical",
}


def department_for(db: Session, issue_type: IssueType) -> Department | None:
    return db.query(Department).filter(Department.name == ISSUE_TO_DEPARTMENT[issue_type]).first()
