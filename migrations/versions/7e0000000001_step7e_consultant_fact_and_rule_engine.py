"""Step 7E consultant fact and rule engine schema

Revision ID: 7e0000000001
Revises: 36df5eb0fed7
Create Date: 2026-09-21 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e0000000001'
down_revision = '36df5eb0fed7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Update facts table
    with op.batch_alter_table('facts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fact_key', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('data_type', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('origin', sa.String(length=30), nullable=True))
        batch_op.create_unique_constraint(batch_op.f('uq_facts_fact_key'), ['fact_key'])

    # 2. Update rules table
    with op.batch_alter_table('rules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rule_id', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=False, server_default='50'))
        batch_op.add_column(sa.Column('conditions_json', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('match_operator', sa.String(length=10), nullable=False, server_default='ALL'))
        batch_op.add_column(sa.Column('conclusion_en', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('conclusion_km', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('advice_en', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('advice_km', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('knowledge_refs', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.create_unique_constraint(batch_op.f('uq_rules_rule_id'), ['rule_id'])


def downgrade():
    with op.batch_alter_table('rules', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_rules_rule_id'), type_='unique')
        batch_op.drop_column('is_active')
        batch_op.drop_column('knowledge_refs')
        batch_op.drop_column('advice_km')
        batch_op.drop_column('advice_en')
        batch_op.drop_column('conclusion_km')
        batch_op.drop_column('conclusion_en')
        batch_op.drop_column('match_operator')
        batch_op.drop_column('conditions_json')
        batch_op.drop_column('priority')
        batch_op.drop_column('category')
        batch_op.drop_column('rule_id')

    with op.batch_alter_table('facts', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_facts_fact_key'), type_='unique')
        batch_op.drop_column('origin')
        batch_op.drop_column('data_type')
        batch_op.drop_column('category')
        batch_op.drop_column('fact_key')
