import pytest
from pyspark.sql import Row
from src.glue.transformations import GenericTransformer
from src.glue.utils import DataQualityGate

def test_phi_masking(spark):
    sample_data = [
        Row(emp_id="E001", ssn="123-45-6789", email="john.doe@hospital.org", phone_number="555-0199")
    ]
    df = spark.createDataFrame(sample_data)
    schema_cfg = [
        {"name": "ssn", "phi_mask": True},
        {"name": "email", "phi_mask": True},
        {"name": "phone_number", "phi_mask": True}
    ]
    masked_df = GenericTransformer.mask_phi(df, schema_cfg, id_col="emp_id")

    assert "ssn" not in masked_df.columns
    assert "email" not in masked_df.columns
    assert "phone_number" not in masked_df.columns
    rows = masked_df.collect()
    assert rows[0]["masked_ssn"] == "***-6789"
    assert len(rows[0]["ssn_hash"]) == 64

def test_referential_integrity(spark):
    employees = [Row(emp_id="E1"), Row(emp_id="E2")]
    tests = [Row(test_id="T1", emp_id="E1"), Row(test_id="T2", emp_id="E999")]

    emp_df = spark.createDataFrame(employees)
    test_df = spark.createDataFrame(tests)

    valid_df, orphans_df = DataQualityGate.check_referential_integrity(
        child_df=test_df, parent_df=emp_df, fk="emp_id", pk="emp_id"
    )

    assert valid_df.count() == 1
    assert orphans_df.count() == 1
    assert orphans_df.collect()[0]["emp_id"] == "E999"