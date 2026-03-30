"""
Import all models so SQLAlchemy mappers are fully configured
before any query is executed.
"""
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.sprint import Sprint  # noqa: F401
from app.models.sprint_member_performance import SprintMemberPerformance  # noqa: F401
from app.models.project_plan import ProjectPlan  # noqa: F401
