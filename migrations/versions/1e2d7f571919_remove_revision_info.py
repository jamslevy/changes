"""Remove revision information from Change

Revision ID: 1e2d7f571919
Revises: 3ab6b0898a24
Create Date: 2013-09-30 17:17:40.350381

"""

# revision identifiers, used by Alembic.
revision = '1e2d7f571919'
down_revision = '3ab6b0898a24'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('change', u'revision_sha')
    op.drop_column('change', u'parent_revision_sha')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('change', sa.Column(u'parent_revision_sha', sa.VARCHAR(length=40), nullable=True))
    op.add_column('change', sa.Column(u'revision_sha', sa.VARCHAR(length=40), nullable=True))
    ### end Alembic commands ###