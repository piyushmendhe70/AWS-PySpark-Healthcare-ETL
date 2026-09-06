"""
conftest.py: Shared PySpark Test Harness Fixture
Spins up a lightweight local SparkSession for unit testing.
"""

import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    spark_session = (
        SparkSession.builder
        .master("local[2]")
        .appName("EHS-UnitTest-Harness")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield spark_session
    spark_session.stop()