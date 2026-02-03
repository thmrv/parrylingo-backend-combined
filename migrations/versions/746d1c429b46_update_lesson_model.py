"""

Revision ID: 746d1c429b46
Revises: f461445456ad
Create Date: 2025-05-28 19:40:46.447177

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "746d1c429b46"
down_revision: Union[str, None] = "f461445456ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Убираем старый unique-constraint, если есть
    op.drop_constraint(op.f("uq_language_code"), "language", type_="unique")
    op.create_unique_constraint(
        op.f("uq_language_language_code"), "language", ["language_code"]
    )

    # Добавляем nullable=True временно
    op.add_column("lesson", sa.Column("is_block", sa.Boolean(), nullable=True))
    op.add_column("lesson", sa.Column("lesson_id_mobile", sa.String(), nullable=True))

    # Устанавливаем значение по умолчанию для уже существующих строк
    op.execute("UPDATE lesson SET is_block = FALSE")

    # Меняем колонку на NOT NULL
    with op.batch_alter_table("lesson") as batch_op:
        batch_op.alter_column("is_block", nullable=False)


def downgrade() -> None:
    op.drop_column("lesson", "is_block")
    op.drop_column("lesson", "lesson_id_mobile")
    op.drop_constraint(op.f("uq_language_language_code"), "language", type_="unique")
    op.create_unique_constraint(
        op.f("uq_language_code"),
        "language",
        ["language_code"],
        postgresql_nulls_not_distinct=False,
    )
