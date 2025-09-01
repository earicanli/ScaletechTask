import requests
import pandas as pd
from datetime import date
from google.cloud import bigquery

from src.api.models import PyPIPackage, PyPIPackageDownloadCount


class PyPIBigQuery:
    def __init__(self):

        self.client = bigquery.Client()
        self.sources = {
            'download_statistics': {
                'project_id': "bigquery-public-data",
                'dataset_id': "pypi",
                'table_id': "file_downloads"
        },
            'project_metadata': {
                'project_id': "bigquery-public-data",
                'dataset_id': "pypi",
                'table_id': "distribution_metadata"
            }
        }

    def get_table_ref(self, target):
        try:
            src = self.sources[target]
            return f"{src['project_id']}.{src['dataset_id']}.{src['table_id']}"
        except KeyError:
            raise ValueError('Unknown target')

    def _pull_package_download_counts(self, pkgs: str | list[str],
                                      include_country: bool = False,
                                      include_version: bool = False,
                                      upper_date_bound: date | None = None,
                                      lower_date_bound: date | None = None):

        table_ref = self.get_table_ref('download_statistics')

        select_cols = [
            "project",
            "DATE(timestamp) AS timestamp",
            "COUNT(*) AS download_count"]

        group_cols = ["project", "timestamp"]
        order_cols = ["project DESC", "timestamp DESC"]

        if include_country:
            select_cols.append("country_code")
            group_cols.append("country_code")
            order_cols.append("country_code DESC")

        if include_version:
            select_cols.append("file.version")
            group_cols.append("file.version")
            order_cols.append("file.version DESC")

        if isinstance(pkgs, str):
            where_conds = [f"file.project = '{pkgs}'"]
        else:
            pkgs_list = ", ".join(f"'{p}'" for p in pkgs)
            where_conds = [f"file.project IN ({pkgs_list})"]

        if lower_date_bound:
            where_conds.append(f"DATE(timestamp) >= DATE('{lower_date_bound.isoformat()}')")

        if upper_date_bound:
            where_conds.append(f"DATE(timestamp) <= DATE('{upper_date_bound.isoformat()}')")

        q = f"""
        SELECT {", ".join(select_cols)}
        FROM `{table_ref}`
        WHERE {" AND ".join(where_conds)}
        GROUP BY {", ".join(group_cols)}
        ORDER BY {", ".join(order_cols)}
        ;
        """

        job = self.client.query(q)
        return job.to_dataframe()

    @staticmethod
    def _validate_raw_data(raw_df):
        res = [dict(PyPIPackageDownloadCount(**row))
               for row in raw_df.to_dict(orient="records")]
        return pd.DataFrame(res)

    def get_package_download_counts(self, pkgs: str | list[str],
                                    include_country: bool = False,
                                    include_version: bool = False,
                                    upper_date_bound: date | None = None,
                                    lower_date_bound: date | None = None):

        raw_df = self._pull_package_download_counts(pkgs=pkgs,
                                                    include_country=include_country,
                                                    include_version=include_version,
                                                    upper_date_bound=upper_date_bound,
                                                    lower_date_bound=lower_date_bound)
        return self._validate_raw_data(raw_df)


class PyPIJSONApi:

    def __init__(self):
        self.base_url = "https://pypi.org/"

    def _pull_raw_package_metadata(self, pkg):
        partial_endpoint = f"pypi/{pkg}/json"
        full_endpoint = self.base_url + partial_endpoint
        res = requests.get(full_endpoint)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def _validate_raw_data(raw_data):
        return PyPIPackage(**raw_data)

    def get_package_metadata(self, pkg):
        raw_data = self._pull_raw_package_metadata(pkg)
        return self._validate_raw_data(raw_data)
