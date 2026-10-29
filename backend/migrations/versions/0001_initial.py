"""Initial schema. Frozen explicit DDL; no runtime model imports."""
from alembic import op
import sqlalchemy as sa
revision='0001'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('users',sa.Column('id',sa.Integer,primary_key=True),sa.Column('email',sa.String(254),nullable=False),sa.Column('name',sa.String(100),nullable=False),sa.Column('password_hash',sa.String(255),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_users_email','users',['email'],unique=True)
    op.create_table('sessions',sa.Column('token_hash',sa.String(64),primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('expires_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_sessions_user_id','sessions',['user_id'])
    op.create_table('fields',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('name',sa.String(100),nullable=False),sa.Column('crop',sa.String(100),nullable=False),sa.Column('area',sa.Float,nullable=False),sa.Column('location',sa.String(200),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_fields_user_id','fields',['user_id'])
    op.create_table('scans',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('field_id',sa.Integer,sa.ForeignKey('fields.id')),sa.Column('image_key',sa.String(80),nullable=False),sa.Column('notes',sa.String(2000),nullable=False),sa.Column('prediction',sa.JSON,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_scans_user_id','scans',['user_id']);op.create_index('ix_scans_field_id','scans',['field_id'])
    op.create_table('followups',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('scan_id',sa.Integer,sa.ForeignKey('scans.id'),nullable=False),sa.Column('due_at',sa.DateTime(timezone=True),nullable=False),sa.Column('done',sa.Boolean,nullable=False))
    op.create_index('ix_followups_user_id','followups',['user_id']);op.create_index('ix_followups_due_at','followups',['due_at'])
def downgrade():
    for table in ['followups','scans','fields','sessions','users']:op.drop_table(table)
