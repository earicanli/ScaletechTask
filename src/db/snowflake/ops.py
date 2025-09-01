import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.api.models import PyPIPackage
from src.db.snowflake.models import (
    Base, 
    PyPIPackages, 
    PyPIPackageReleases, 
    # PyPIDependencies
)

def get_engine():

    user = os.environ["SNOWFLAKE_USER"]
    password = os.environ["SNOWFLAKE_PASSWORD"]
    account = os.environ["SNOWFLAKE_ACCOUNT"]
    database = os.environ["SNOWFLAKE_DATABASE"]
    schema = os.environ["SNOWFLAKE_SCHEMA"]

    engine_url = f"snowflake://{user}:{password}@{account}/{database}/{schema}"
    engine = create_engine(engine_url)
    return engine


def init_schema(engine, schema_name):

    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        conn.execute(text(f"USE SCHEMA {schema_name}"))
        Base.metadata.create_all(bind=conn)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def insert_pypi_package(md, session):

    # Insert top-level package metadata
    pkg_row = PyPIPackages(
        package_name=md.name,
        version=md.version,
        summary=md.summary,
        github_url=md.github_url,
        github_owner=md.github_owner,
        github_repo_name=md.github_repo_name,
        github_repo_name_full=md.github_repo_name_full,
        pulled_dt=md.snapshot_dt
    )
    session.add(pkg_row)

    # Insert releases
    # bulk insert releases
    if md.releases:
        session.bulk_save_objects([
            PyPIPackageReleases(
                package_name=md.name,
                version=r.version,
                release_dt=r.release_dt,
                source_size=r.source_size
            ) for r in md.releases
        ])

    # Insert dependencies
    # for dep in md.dependencies or []:
    #     dep_row = PyPIDependencies(
    #         package_name=md.name,
    #         dependency=dep
    #     )
    #     session.add(dep_row)

    # Commit
    session.commit()
