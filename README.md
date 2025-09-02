# Scaletech Task

### Objective

Build a data pipeline to collect and prepare data about data engineering
technologies for downstream analytics teams.

- **Data Sources**:
  - GitHub API
  - PyPI API
- **Target Packages**:
  - Apache Airflow
  - dbt
  - Apache Spark
  - Pandas
  - SQLAlchemy
  - Great Expectations
  - Prefect
  - Apache Kafka
  - Snowflake-connector-python
  - DuckDB

### Codebase:

```
ScaletechTask
├── notebooks
│   ├── pypi_bigquery_explore.ipynb   # Exploratory script for BigQuery
│   └── pypi_json_api_explore.ipynb   # Exploratory script for PyPI JSON API
├── src
│   ├── api
│   │   ├── github.py                 # GitHub API wrapper (Repo endpoint only)
│   │   ├── models.py                 # Pydantic models for API output validation
│   │   └── pypi.py                   # PyPI JSON API & BigQuery dataset wrapper
│   ├── db
│   │   ├── bigquery
│   │   │   └── utils.py              # BigQuery helpers & query cost estimator
│   │   └── snowflake
│   │       ├── models.py             # SQLAlchemy ORM models for DB tables
│   │       └── ops.py                # Schema init & insert functions
│   ├── utils
│   │   ├── misc.py                   # Helper functions for JSON API (dict walking/display)
│   │   └── size_units.py             # String coercion for size units
│   └── main.py                       # Data pipeline script
├── .env_sample                       # Dotenv template (rename to .env & fill out)
├── README.md                         # What youre reading right now!
└── requirements.txt                  # Python package dependencies
```

### Process:

As (mostly) visible in src.main:

- Environmental variables are read in from .env file, these being:
  - Snowflake credentials, DB, and schema
  - Google application credentials json path (for BigQuery)
- Table schema is initialized in DB (if not already existing), SQLAlchemy engine / session / objects made available. 
- Target packages are listed as their respective endpoint stems (as seen in PyPI URL).
- Data is pulled, read from each source & written:
  1) **PyPI JSON API**: Looping over packages, API request is made (via API wrapper), validated, and is written to DB.
      - Writes to **PYPI_PACKAGES** and **PYPI_PACKAGE_RELEASES**
  2) **PyPI BigQuery Dataset**: Query is carried out for all packages at once, is validated, and written to DB.
      - Writes to **PYPI_DOWNLOAD_COUNTS**
  3) **GitHub API**: Looping over packages, GitHub owner/repo are pulled from the corresponding entry in **PYPI_PACKAGES**.
                     These are then fed into GitHub API (via API wrapper), validated, and written to the DB.
      - Writes to **GITHUB_REPOS**

### Database:

##### PYPI_PACKAGES
| Column                   | Type         | Constraints | Description                           |
| ------------------------ | ------------ | ----------- | ------------------------------------- |
| PACKAGE\_NAME            | VARCHAR(500) | PRIMARY KEY | Name of the PyPI package              |
| VERSION                  | VARCHAR(500) | NOT NULL    | Current package version               |
| SUMMARY                  | VARCHAR(500) | NULLABLE    | Package summary/description           |
| GITHUB\_URL              | VARCHAR(500) | NULLABLE    | URL of associated GitHub repository   |
| GITHUB\_OWNER            | VARCHAR(500) | NULLABLE    | Owner of the GitHub repository        |
| GITHUB\_REPO\_NAME       | VARCHAR(500) | NULLABLE    | Repository name (without owner)       |
| GITHUB\_REPO\_NAME\_FULL | VARCHAR(500) | NULLABLE    | Full repository name (owner/repo)     |
| PULLED\_DT               | TIMESTAMP    | NOT NULL    | Datetime when package data was pulled |

##### PYPI_PACKAGE_RELEASES
| Column        | Type                    | Constraints                                              | Description                          |
| ------------- | ----------------------- |----------------------------------------------------------| ------------------------------------ |
| PACKAGE\_NAME | VARCHAR(500)            | PART OF PRIMARY KEY<br>FK → PYPI\_PACKAGES(PACKAGE\_NAME) | Name of the package                  |
| VERSION       | VARCHAR(500)            | PART OF PRIMARY KEY<br>NOT NULL                          | Version of the package release       |
| RELEASE\_DT   | TIMESTAMP WITH TIMEZONE | NOT NULL                                                 | Release datetime                     |
| SOURCE\_SIZE  | INTEGER                 | NOT NULL                                                 | Size of source distribution in bytes |

##### PYPI_DOWNLOAD_COUNTS
| Column          | Type         | Constraints                                  | Description                           |
| --------------- | ------------ |----------------------------------------------| ------------------------------------- |
| ID              | INTEGER      | PRIMARY KEY<br>AUTOINCREMENT                 | Surrogate key for record              |
| PACKAGE\_NAME   | VARCHAR(500) | FK → PYPI\_PACKAGES(PACKAGE\_NAME)           | Name of the package                   |
| DT              | DATE         | NOT NULL                                     | Date of download count                |
| DOWNLOAD\_COUNT | INTEGER      | NOT NULL                                     | Number of downloads                   |
| VERSION         | VARCHAR(500) | NULLABLE                                     | Optional package version              |
| COUNTRY\_CODE   | VARCHAR(500) | NULLABLE                                     | Country code for download counts      |

Note:
- Unique Constraint on PACKAGE\_NAME + DT + VERSION + COUNTRY\_CODE

##### GITHUB_REPOS
| Column              | Type                    | Constraints                     | Description                       |
| ------------------- | ----------------------- | ------------------------------- | --------------------------------- |
| SNAPSHOT\_DT        | TIMESTAMP WITH TIMEZONE | PRIMARY KEY                     | Snapshot timestamp of repo data   |
| REPO\_NAME          | VARCHAR(500)            | PRIMARY KEY                     | Repository name (without owner)   |
| REPO\_NAME\_FULL    | VARCHAR(500)            | NOT NULL                        | Full repository name (owner/repo) |
| REPO\_URL           | VARCHAR(500)            | NOT NULL                        | Repository URL                    |
| DESCRIPTION         | VARCHAR(500)            | NULLABLE                        | Repo description                  |
| FORKS\_COUNT        | INTEGER                 | NOT NULL                        | Number of forks                   |
| STARGAZERS\_COUNT   | INTEGER                 | NOT NULL                        | Number of stars                   |
| SUBSCRIBERS\_COUNT  | INTEGER                 | NOT NULL                        | Number of subscribers/watchers    |
| OPEN\_ISSUES\_COUNT | INTEGER                 | NOT NULL                        | Number of open issues             |
| CREATED\_AT         | TIMESTAMP WITH TIMEZONE | NOT NULL                        | Repo creation timestamp           |
| UPDATED\_AT         | TIMESTAMP WITH TIMEZONE | NOT NULL                        | Last update timestamp             |
| PUSHED\_AT          | TIMESTAMP WITH TIMEZONE | NOT NULL                        | Last push timestamp               |

Note:
- Unique Constraint on REPO\_NAME\_FULL + SNAPSHOT\_DT
- Wanted REPO_NAME_FULL as FK to PYPI_PACKAGES, but couldnt to nullable GITHUB_* fields in. 
- TOPICS was intended to be included, but had issues with VARIANT in SQLAlchemy (see below)

---

### Remarks:

- **Validation** here happens under the hood per class, as part of each class' get_{TARGET} method. Internally, a private
  _validate_raw_data method is called, which feeds the data through the corresponding Pydantic model.
- **BigQuery results** here (as seen in **PYPI_DOWNLOAD_COUNTS**) is limited due to pricing / query times.
  - Columns **VERSION** and **COUNTRY_CODE** are fully NULL due to this, but the functionality is there to pull them.
  - Data is limited to this year.
- **Snowflake** caused me a couple headaches as was my first time using it. Two points for me are:
  - I was not aware of the non-need for traditional indexes (as seen by my commented out Index setting in the ORM Models).
  - I also was not aware that PKs & unique constraints are applicable, but not enforced. Therefore, some uniqueness 
    measure would need to be put in place.
  - I was unable to get sqlalchemy.dialects.snowflake working, therefore I couldnt get VARIANT fields working, therefore 
    causing me to ditch a couple fields.


 






