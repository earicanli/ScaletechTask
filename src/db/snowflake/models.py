from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Index,
    ForeignKey,
    PrimaryKeyConstraint,
    UniqueConstraint,
)

# from sqlalchemy.dialects.snowflake import VARIANT  # cant find...
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PyPIPackages(Base):
    __tablename__ = "PYPI_PACKAGES"

    package_name = Column("PACKAGE_NAME", String(500), primary_key=True)
    version = Column("VERSION", String(500), nullable=False)
    summary = Column("SUMMARY", String(500), nullable=True)
    github_url = Column("GITHUB_URL", String(500), nullable=True)
    github_owner = Column("GITHUB_OWNER", String(500), nullable=True)
    github_repo_name = Column("GITHUB_REPO_NAME", String(500), nullable=True)
    github_repo_name_full = Column("GITHUB_REPO_NAME_FULL", String(500), nullable=True)
    pulled_dt = Column("PULLED_DT", DateTime, nullable=False)

    # Indexes are not part of standard tables in Snowflake - only hybrid tables!
    # __table_args__ = (
    #     Index("ix_pypi_github_repo_fullname", "GITHUB_REPO_NAME_FULL"),
    #     Index("ix_pypi_package_name", "PACKAGE_NAME"),
    # )

    releases = relationship("PyPIPackageReleases", back_populates="package")
    downloads = relationship("PyPIDownloadCounts", back_populates="package")
    # dependencies = relationship("PyPIPackages", back_populates="package")

    # cant guarantee github entires in pypi not null, cant key
    # github_repos = relationship("GitHubRepos", back_populates="packages")


class PyPIPackageReleases(Base):
    __tablename__ = "PYPI_PACKAGE_RELEASES"

    package_name = Column("PACKAGE_NAME", String(500), ForeignKey("PYPI_PACKAGES.PACKAGE_NAME"))
    version = Column("VERSION", String(500), nullable=False)
    release_dt = Column("RELEASE_DT", DateTime(timezone=True), nullable=False)
    source_size = Column("SOURCE_SIZE", Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "PACKAGE_NAME",
            "VERSION",
            name="PK_PYPI_PACKAGE_RELEASES_PK"
        ),
    )

    package = relationship("PyPIPackages", back_populates="releases")

# class PyPIDependencies(Base):
#     __tablename__ = "PYPI_DEPENDENCIES"
#
#     id = Column("ID", Integer, primary_key=True, autoincrement=True)
#     package_name = Column("PACKAGE_NAME", String(500), ForeignKey("pypi_packages.package_name"))
#     dependency = Column("DEPENDENCY", String(500), nullable=False)
#
#     package = relationship("PyPIPackages", back_populates="dependencies")


class PyPIDownloadCounts(Base):
    __tablename__ = "PYPI_DOWNLOAD_COUNTS"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Surrogate - temporary!

    package_name = Column("PACKAGE_NAME", String(500), ForeignKey("PYPI_PACKAGES.PACKAGE_NAME"))
    dt = Column("DT", Date, nullable=False)
    download_count = Column("DOWNLOAD_COUNT", Integer, nullable=False)
    version = Column("VERSION", String(500), nullable=True)
    country_code = Column("COUNTRY_CODE", String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "PACKAGE_NAME",
            "DT",
            "VERSION",
            "COUNTRY_CODE",
            name="UQ_PYPI_DOWNLOAD_COUNTS"
        ),
        # Indexes are not part of standard tables in Snowflake - only hybrid tables!
        # Index("ix_downloads_w_version", "PACKAGE_NAME", "DT", "VERSION"),
        # Index("ix_downloads_w_country", "PACKAGE_NAME", "DT", "COUNTRY_CODE"),
        # Index("ix_downloads_w_version_country", "PACKAGE_NAME", "DT", "VERSION", "COUNTRY_CODE")
    )

    package = relationship("PyPIPackages", back_populates="downloads")


class GitHubRepos(Base):
    __tablename__ = 'GITHUB_REPOS'

    snapshot_dt = Column("SNAPSHOT_DT", DateTime(timezone=True), primary_key=True, nullable=False)
    repo_name = Column("REPO_NAME", String(500), primary_key=True, nullable=False)
    repo_name_full = Column("REPO_NAME_FULL", String(500), nullable=False)
    repo_url = Column("REPO_URL", String(500), nullable=False)
    description = Column("DESCRIPTION", String(500), nullable=True)
    forks_count = Column("FORKS_COUNT", Integer, nullable=False)
    stargazers_count = Column("STARGAZERS_COUNT", Integer, nullable=False)
    subscribers_count = Column("SUBSCRIBERS_COUNT", Integer, nullable=False)
    open_issues_count = Column("OPEN_ISSUES_COUNT", Integer, nullable=False)
    # topics = Column("TOPICS", VARIANT, nullable=False, default=[])
    created_at = Column("CREATED_AT", DateTime(timezone=True), nullable=False)
    updated_at = Column("UPDATED_AT", DateTime(timezone=True), nullable=False)
    pushed_at = Column("PUSHED_AT", DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("REPO_NAME_FULL", "SNAPSHOT_DT", name="uq_fullname_snapshot"),
        # Indexes are not part of standard tables in Snowflake - only hybrid tables!
        # Index("ix_github_fullname", "REPO_NAME_FULL", "SNAPSHOT_DT"),
    )

    # cant guarantee github entires in pypi not null, cant key
    # packages = relationship("PyPIPackages", back_populates="github_repos")


