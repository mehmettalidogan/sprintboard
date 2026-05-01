"""align_project_models_and_sprint_project_id

Revision ID: 8f2c7a9d4b1e
Revises: 67ab13989207
Create Date: 2026-04-30 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8f2c7a9d4b1e"
down_revision: Union[str, None] = "67ab13989207"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep this migration idempotent because some local databases were partially
    # advanced by Base.metadata.create_all before migrations were committed.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS github_username VARCHAR(255)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR,
            owner_id UUID NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(owner_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_id ON projects (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects (owner_id)")

    op.execute("ALTER TABLE sprints ADD COLUMN IF NOT EXISTS project_id UUID")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sprints_project_id ON sprints (project_id)")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'sprints_project_id_fkey'
            ) THEN
                ALTER TABLE sprints
                ADD CONSTRAINT sprints_project_id_fkey
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS project_plans (
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            project_idea VARCHAR NOT NULL,
            sprint_count INTEGER NOT NULL,
            team_members VARCHAR[] NOT NULL,
            plan_data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_plans_id ON project_plans (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_plans_user_id ON project_plans (user_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID NOT NULL,
            title VARCHAR(255) NOT NULL,
            description VARCHAR,
            status VARCHAR(50) NOT NULL,
            nlp_complexity_score DOUBLE PRECISION NOT NULL,
            deadline DATE,
            sprint_id UUID NOT NULL,
            assignee_id UUID,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(sprint_id) REFERENCES sprints (id) ON DELETE CASCADE,
            FOREIGN KEY(assignee_id) REFERENCES users (id) ON DELETE SET NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_id ON tasks (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_sprint_id ON tasks (sprint_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_assignee_id ON tasks (assignee_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tasks_assignee_id")
    op.execute("DROP INDEX IF EXISTS ix_tasks_sprint_id")
    op.execute("DROP INDEX IF EXISTS ix_tasks_id")
    op.execute("DROP TABLE IF EXISTS tasks")

    op.execute("DROP INDEX IF EXISTS ix_project_plans_user_id")
    op.execute("DROP INDEX IF EXISTS ix_project_plans_id")
    op.execute("DROP TABLE IF EXISTS project_plans")

    op.execute("ALTER TABLE sprints DROP CONSTRAINT IF EXISTS sprints_project_id_fkey")
    op.execute("DROP INDEX IF EXISTS ix_sprints_project_id")
    op.execute("ALTER TABLE sprints DROP COLUMN IF EXISTS project_id")

    op.execute("DROP INDEX IF EXISTS ix_projects_owner_id")
    op.execute("DROP INDEX IF EXISTS ix_projects_id")
    op.execute("DROP TABLE IF EXISTS projects")

    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS github_username")
