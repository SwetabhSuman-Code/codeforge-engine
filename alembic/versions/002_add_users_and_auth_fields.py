"""add_users_and_auth_fields

Revision ID: 002_add_users_and_auth_fields
Revises: 001_baseline_schema
Create Date: 2026-07-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_users_and_auth_fields'
down_revision: Union[str, None] = '001_baseline_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    op.add_column('problems', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_problems_created_by_users', 'problems', 'users', ['created_by'], ['id'])

    op.add_column('submissions', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_submissions_owner_id_users', 'submissions', 'users', ['owner_id'], ['id'])
    op.create_foreign_key('fk_submissions_problem_id_problems', 'submissions', 'problems', ['problem_id'], ['id'])

    op.create_foreign_key('fk_testcases_problem_id_problems', 'testcases', 'problems', ['problem_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_testcases_problem_id_problems', 'testcases', type_='foreignkey')
    op.drop_constraint('fk_submissions_problem_id_problems', 'submissions', type_='foreignkey')
    op.drop_constraint('fk_submissions_owner_id_users', 'submissions', type_='foreignkey')
    op.drop_column('submissions', 'owner_id')
    op.drop_constraint('fk_problems_created_by_users', 'problems', type_='foreignkey')
    op.drop_column('problems', 'created_by')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
