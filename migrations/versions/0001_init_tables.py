"""init tables

Revision ID: 0001
Revises:
Create Date: 2026-08-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("query", sa.String(255), nullable=False),
        sa.Column("source_types", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="stopped"),
        sa.Column("report_id", sa.String(64), nullable=True),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=3), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(3)")),
        sa.Column("updated_at", mysql.DATETIME(fsp=3), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(3)")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_status", "search_tasks", ["status"])
    op.create_index("idx_query", "search_tasks", ["query"])
    op.create_index("idx_created", "search_tasks", ["created_at"])

    op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", mysql.DATETIME(fsp=3), nullable=True),
        sa.Column("created_at", mysql.DATETIME(fsp=3), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(3)")),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_task_type", "sources", ["task_id", "source_type"])
    op.create_index("idx_type", "sources", ["source_type"])

    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.String(64), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("created_at", mysql.DATETIME(fsp=3), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(3)")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_topic", "reports", ["topic"])
    op.create_index("idx_created", "reports", ["created_at"])

    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.String(64), nullable=False),
        sa.Column("node_id", sa.String(64), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("ref", sa.String(1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id", "node_id", name="uk_report_node"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_report", "graph_nodes", ["report_id"])

    op.create_table(
        "graph_edges",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("target", sa.String(64), nullable=False),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("ref", sa.String(1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_report", "graph_edges", ["report_id"])
    op.create_index("idx_src_tgt", "graph_edges", ["source", "target"])

    op.create_table(
        "forum_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ts", mysql.DATETIME(fsp=3), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("task_status", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_ts", "forum_logs", ["ts"])
    op.create_index("idx_task_status", "forum_logs", ["task_status"])


def downgrade() -> None:
    op.drop_table("forum_logs")
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
    op.drop_table("reports")
    op.drop_table("sources")
    op.drop_table("search_tasks")
