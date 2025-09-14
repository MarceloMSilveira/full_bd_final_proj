"""Backfill genres for artists and venues

Revision ID: 2cb1322c8889
Revises: fa9721d14385
Create Date: 2025-09-14 11:32:39.335584

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# IDs da migração
revision = "2cb1322c8889"
down_revision = "fa9721d14385"
branch_labels = None
depends_on = None

# >>> Ajuste aqui se necessário <<<
ARTISTS_TABLE = '"Artist"'   # ou '"Artist"' se sua tabela tem maiúscula/aspas
VENUES_TABLE  = '"Venue"'    # ou '"Venue"'
SRC = 'genres_old'          # coluna texto: 'rock,samba,jazz'
DST = 'genres'              # coluna ARRAY(TEXT)

BACKFILL_SQL = """
    UPDATE {table}
    SET {dst} = CASE
        WHEN {src} IS NULL OR btrim({src}) = '' THEN ARRAY[]::text[]
        ELSE array_remove(
               ARRAY(
                 SELECT btrim(x)
                 FROM unnest(string_to_array({src}, ',')) AS x
               ),
               ''
             )
    END
    WHERE {dst} IS NULL;
"""

ROLLBACK_SQL = """
    UPDATE {table}
    SET {src} = CASE
        WHEN {dst} IS NULL THEN NULL
        ELSE array_to_string({dst}, ',')
    END
    WHERE {src} IS NULL;
"""

def upgrade():
    # Backfill em ambas as tabelas, sem sobrescrever registros já preenchidos
    op.execute(BACKFILL_SQL.format(table=ARTISTS_TABLE, src=SRC, dst=DST))
    op.execute(BACKFILL_SQL.format(table=VENUES_TABLE,  src=SRC, dst=DST))

def downgrade():
    # Reconstroi a coluna string a partir do ARRAY (sem sobrescrever quem já tem texto)
    op.execute(ROLLBACK_SQL.format(table=ARTISTS_TABLE, src=SRC, dst=DST))
    op.execute(ROLLBACK_SQL.format(table=VENUES_TABLE,  src=SRC, dst=DST))

