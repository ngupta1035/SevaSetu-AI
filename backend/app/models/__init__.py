# Import every model so Alembic autogenerate sees them.
from app.models.user import User
from app.models.department import Department
from app.models.issue import CivicIssue, IssueReport
from app.models.assignment import Assignment
from app.models.resolution import Resolution
from app.models.issue_event import IssueEvent
from app.models.ai_prediction import AIPrediction
from app.models.duplicate_candidate import DuplicateCandidate

__all__ = ["User", "Department", "CivicIssue", "IssueReport", "Assignment",
           "Resolution", "IssueEvent", "AIPrediction", "DuplicateCandidate"]
