"""

Revision ID: 56df8ed2e1ff
Revises: 55fa062a8c54
Create Date: 2025-06-04 07:23:00.808321

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "56df8ed2e1ff"
down_revision: Union[str, None] = "55fa062a8c54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. сначала переименовываем колонку
    op.alter_column("word", "title", new_column_name="titles")

    # 2. затем меняем тип и явно указываем, как кастовать
    op.alter_column(
        "word",
        "titles",
        existing_type=sa.VARCHAR(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="titles::jsonb",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "word",
        "titles",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.VARCHAR(),
        postgresql_using="titles::text",
        existing_nullable=False,
    )

    op.alter_column("word", "titles", new_column_name="title")
