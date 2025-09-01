import os
from datetime import date
from dotenv import load_dotenv

from src.api.models import GitHubRepo
from src.api.pypi import PyPIJSONApi, PyPIBigQuery
from src.api.github import GitHubAPI
from src.db.snowflake.ops import (
    init_schema,
    get_engine,
    get_session,
    insert_pypi_package
)
from src.db.snowflake.models import PyPIDownloadCounts, PyPIPackages, GitHubRepos


if __name__ == '__main__':

    load_dotenv()

    engine = get_engine()
    session = get_session(engine)
    init_schema(engine, schema_name=os.environ.get('SNOWFLAKE_SCHEMA'))

    packages = [
        'apache-airflow',
        'dbt',
        'pyspark',
        'pandas',
        'SQLAlchemy',
        'great-expectations',
        'prefect',
        'kafka-python',
        'snowflake-connector-python',
        'duckdb',
        'google-cloud-bigquery'
    ]

    # print('------------------------------------------')
    # print('Getting package metadata via PyPI JSON API')
    # print('------------------------------------------')
    # for pkg in packages:
    #     print(pkg)
    #     print('- Pulling data...')
    #     md = PyPIJSONApi().get_package_metadata(pkg)
    #     print('- Writing to DB...')
    #     insert_pypi_package(md, session)
    #     print('- Done!')

    print('-------------------------------------------------')
    print('Getting package download data via PyPI BQ Dataset')
    print('-------------------------------------------------')
    dl_stats = PyPIBigQuery().get_package_download_counts(
        pkgs=packages,
        include_version=True,
        include_country=True,
        lower_date_bound=date(2025, 1, 1)
    )
    dl_stats.to_sql(
        name=PyPIDownloadCounts.__tablename__,
        con=engine,
        schema=os.environ.get('SNOWFLAKE_SCHEMA'),
        index=False,
        if_exists='append',
        method='multi'
    )

    # print('-------------------------------------')
    # print('Getting repo data via GitHub Rest API')
    # print('-------------------------------------')
    # for pkg in packages:
    #     print(pkg)
    #     print('- Getting previously found GitHub info...')
    #     res = (
    #         session.query(
    #             PyPIPackages.github_owner,
    #             PyPIPackages.github_repo_name
    #         )
    #         .filter(PyPIPackages.package_name == pkg)
    #         .first()
    #     )
    #
    #     if not res[0]:
    #         print("--> No GitHub for provided package!")
    #         continue
    #
    #     github_owner, github_repo_name = res
    #     print(f"--> Owner/Repo: {github_owner}/{github_repo_name}")
    #
    #     print('- Pulling data...')
    #     api = GitHubAPI()
    #     data = api.get_repo_metadata(owner=github_owner, repo=github_repo_name)
    #     print('- Writing to DB...')
    #     entry = GitHubRepos(**dict(data))
    #     session.add(entry)
    #     session.commit()
    #     print('- Done!')
