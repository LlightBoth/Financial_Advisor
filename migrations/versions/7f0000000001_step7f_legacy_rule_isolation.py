"""Step 7F legacy rule isolation and financial consultant knowledge base activation

Revision ID: 7f0000000001
Revises: 7e0000000001
Create Date: 2026-09-21 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f0000000001'
down_revision = '7e0000000001'
branch_labels = None
depends_on = None

CANONICAL_KB_VERSION = 'financial-kb-v1.0'

CANONICAL_RULE_IDS = (
    'DEFICIT_WITH_DEBT',
    'DEFICIT_NO_DEBT',
    'INCOME_ZERO_UNEMPLOYED',
    'BREAK_EVEN_ZERO_MARGIN',
    'TIGHT_MARGIN_HIGH_EXPENSE',
    'SURPLUS_WITH_DEBT_SERVICING',
    'BALANCED_BUDGET_BUFFER_BUILDING',
    'FLEXIBLE_BUDGET_CAPITAL_GROWTH',
)


def upgrade():
    # 1. Add kb_version column to rules
    with op.batch_alter_table('rules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('kb_version', sa.String(length=50), nullable=True))

    # 2. Add kb_version column to facts
    with op.batch_alter_table('facts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('kb_version', sa.String(length=50), nullable=True))

    # 3. Add kb_version column to histories
    with op.batch_alter_table('histories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('kb_version', sa.String(length=50), nullable=True))

    # 4. Deactivate all legacy rules and ensure kb_version is NULL
    op.execute(
        "UPDATE rules SET is_active = 0, kb_version = NULL "
        "WHERE rule_id IS NULL OR rule_id NOT IN ("
        + ", ".join(f"'{rid}'" for rid in CANONICAL_RULE_IDS)
        + ")"
    )

    # 5. Activate canonical rules and tag with canonical kb_version
    op.execute(
        f"UPDATE rules SET is_active = 1, kb_version = '{CANONICAL_KB_VERSION}' "
        "WHERE rule_id IN ("
        + ", ".join(f"'{rid}'" for rid in CANONICAL_RULE_IDS)
        + ")"
    )

    # 6. Tag canonical facts with canonical kb_version and legacy facts with NULL
    op.execute(
        f"UPDATE facts SET kb_version = '{CANONICAL_KB_VERSION}' "
        "WHERE fact_key IS NOT NULL"
    )
    op.execute(
        "UPDATE facts SET kb_version = NULL WHERE fact_key IS NULL"
    )

    # 7. Existing histories remain kb_version = NULL (zero mutation)


def downgrade():
    with op.batch_alter_table('histories', schema=None) as batch_op:
        batch_op.drop_column('kb_version')

    with op.batch_alter_table('facts', schema=None) as batch_op:
        batch_op.drop_column('kb_version')

    with op.batch_alter_table('rules', schema=None) as batch_op:
        batch_op.drop_column('kb_version')
