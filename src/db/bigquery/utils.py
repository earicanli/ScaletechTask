from google.cloud import bigquery

from src.utils.size_units import coerce_sizing_unit


COST_PER_TERABYTE = 6.25


def get_table_schema(project_id, dataset_id, table_id, bq_client=None):

    if bq_client is None:
        bq_client = bigquery.Client()

    q = f"""
    SELECT
      column_name,
      data_type,
      is_nullable
    FROM
      `{project_id}.{dataset_id}`.INFORMATION_SCHEMA.COLUMNS
    WHERE
      table_name = '{table_id}';
    """

    df = bq_client.query(q).to_dataframe()
    return df


def get_job_size_and_cost(job, size_as='gb'):

    total_bytes_processed = job.total_bytes_processed
    total_bytes_billed = job.total_bytes_billed

    try:
        size_as = coerce_sizing_unit(size_as, to='short')
    except ValueError:
        raise ValueError(f'Invalid "size_as" value: {size_as}')

    unit_conv = {
        'b': 1,
        'kb': 1000,
        'mb': 1000**2,
        'gb': 1000**3,
        'tb': 1000**4
    }

    estimated_cost_usd = (total_bytes_billed / unit_conv['tb']) * COST_PER_TERABYTE

    res = {
        'unit': size_as,
        'n_processed': total_bytes_processed / unit_conv[size_as],
        'n_billed': total_bytes_billed / unit_conv[size_as],
        'cost': estimated_cost_usd
    }

    return res


def get_query_size_and_cost(q, size_as='gb', bq_client=None, dry_run=True):

    if bq_client is None:
        bq_client = bigquery.Client()

    job_cfg = bigquery.QueryJobConfig(dry_run=dry_run)
    job = bq_client.query(q, job_config=job_cfg)
    res = get_job_size_and_cost(job, size_as=size_as)

    return res


def print_query_size_and_cost(size_cost_dict):
    unit = size_cost_dict['unit'].upper()
    print("--- Query Dry Run Results ---")
    print(f"Total {unit} Processed: {size_cost_dict['n_processed']} bytes")
    print(f"Total {unit} Billed: {size_cost_dict['n_billed']} bytes")
    print(f"Estimated Cost: ${size_cost_dict['cost']:.2f} USD")