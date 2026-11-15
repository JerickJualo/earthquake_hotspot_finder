"""Create provenance-safe earthquake and clustering tables.

Revision ID: 0001_initial_schema
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dataset_imports",
        sa.Column("import_id", sa.String(length=120), nullable=False),
        sa.Column("source_name", sa.String(length=80), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("dataset_version", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("import_id"),
    )
    op.create_index("ix_dataset_imports_source_name", "dataset_imports", ["source_name"])
    op.create_index("ix_dataset_imports_status", "dataset_imports", ["status"])

    op.create_table(
        "earthquake_events",
        sa.Column("event_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_id", sa.String(length=120), nullable=False),
        sa.Column("source_name", sa.String(length=80), nullable=False),
        sa.Column("source_event_id", sa.String(length=160), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("depth_km", sa.Float(), nullable=True),
        sa.Column("magnitude", sa.Float(), nullable=True),
        sa.Column("magnitude_type", sa.String(length=30), nullable=True),
        sa.Column("location_description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=True),
        sa.Column("review_status", sa.String(length=40), nullable=True),
        sa.Column("source_network", sa.String(length=40), nullable=True),
        sa.Column("location_source", sa.String(length=40), nullable=True),
        sa.Column("magnitude_source", sa.String(length=40), nullable=True),
        sa.Column("station_count", sa.Float(), nullable=True),
        sa.Column("azimuthal_gap", sa.Float(), nullable=True),
        sa.Column("distance_to_nearest_station", sa.Float(), nullable=True),
        sa.Column("rms_residual", sa.Float(), nullable=True),
        sa.Column("horizontal_error", sa.Float(), nullable=True),
        sa.Column("depth_error", sa.Float(), nullable=True),
        sa.Column("magnitude_error", sa.Float(), nullable=True),
        sa.Column("magnitude_station_count", sa.Float(), nullable=True),
        sa.Column("province_name", sa.String(length=120), nullable=True),
        sa.Column("province_id", sa.String(length=160), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("island_group", sa.String(length=80), nullable=True),
        sa.Column("geographic_assignment_status", sa.String(length=50), nullable=True),
        sa.Column("source_place_is_philippines_label", sa.Boolean(), nullable=True),
        sa.Column("record_validation_status", sa.String(length=50), nullable=True),
        sa.Column("record_validation_reason", sa.Text(), nullable=True),
        sa.Column("source_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["dataset_imports.import_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint(
            "import_id", "source_event_id", name="uq_earthquake_events_import_source_id"
        ),
    )
    op.create_index("ix_earthquake_events_occurred_at", "earthquake_events", ["occurred_at"])
    op.create_index(
        "ix_earthquake_events_latitude_longitude",
        "earthquake_events",
        ["latitude", "longitude"],
    )
    op.create_index("ix_earthquake_events_magnitude", "earthquake_events", ["magnitude"])
    op.create_index("ix_earthquake_events_depth_km", "earthquake_events", ["depth_km"])
    op.create_index("ix_earthquake_events_province_name", "earthquake_events", ["province_name"])
    op.create_index(
        "ix_earthquake_events_geographic_status",
        "earthquake_events",
        ["geographic_assignment_status"],
    )
    op.create_index("ix_earthquake_events_import_id", "earthquake_events", ["import_id"])

    op.create_table(
        "cluster_runs",
        sa.Column("cluster_run_id", sa.String(length=160), nullable=False),
        sa.Column("import_id", sa.String(length=120), nullable=False),
        sa.Column("algorithm", sa.String(length=60), nullable=False),
        sa.Column("n_clusters", sa.Integer(), nullable=False),
        sa.Column("random_state", sa.Integer(), nullable=True),
        sa.Column("silhouette_score", sa.Float(), nullable=True),
        sa.Column("projected_crs", sa.Text(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["dataset_imports.import_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cluster_run_id"),
    )
    op.create_index("ix_cluster_runs_import_id", "cluster_runs", ["import_id"])
    op.create_index("ix_cluster_runs_algorithm", "cluster_runs", ["algorithm"])

    op.create_table(
        "earthquake_cluster_assignments",
        sa.Column("cluster_run_id", sa.String(length=160), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("cluster_label", sa.Integer(), nullable=False),
        sa.Column("projected_x_m", sa.Float(), nullable=True),
        sa.Column("projected_y_m", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["cluster_run_id"], ["cluster_runs.cluster_run_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["earthquake_events.event_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("cluster_run_id", "event_id"),
    )
    op.create_index(
        "ix_cluster_assignments_run_label",
        "earthquake_cluster_assignments",
        ["cluster_run_id", "cluster_label"],
    )
    op.create_index(
        "ix_cluster_assignments_event_id", "earthquake_cluster_assignments", ["event_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_cluster_assignments_event_id", table_name="earthquake_cluster_assignments")
    op.drop_index("ix_cluster_assignments_run_label", table_name="earthquake_cluster_assignments")
    op.drop_table("earthquake_cluster_assignments")
    op.drop_index("ix_cluster_runs_algorithm", table_name="cluster_runs")
    op.drop_index("ix_cluster_runs_import_id", table_name="cluster_runs")
    op.drop_table("cluster_runs")
    op.drop_index("ix_earthquake_events_import_id", table_name="earthquake_events")
    op.drop_index("ix_earthquake_events_geographic_status", table_name="earthquake_events")
    op.drop_index("ix_earthquake_events_province_name", table_name="earthquake_events")
    op.drop_index("ix_earthquake_events_depth_km", table_name="earthquake_events")
    op.drop_index("ix_earthquake_events_magnitude", table_name="earthquake_events")
    op.drop_index("ix_earthquake_events_latitude_longitude", table_name="earthquake_events")
    op.drop_index("ix_earthquake_events_occurred_at", table_name="earthquake_events")
    op.drop_table("earthquake_events")
    op.drop_index("ix_dataset_imports_status", table_name="dataset_imports")
    op.drop_index("ix_dataset_imports_source_name", table_name="dataset_imports")
    op.drop_table("dataset_imports")
