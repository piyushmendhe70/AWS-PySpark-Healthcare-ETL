import pytest
from pyspark.sql import Row
from src.glue.gold import GoldProcessor

def test_fact_tat_and_priority(spark):
    tests = [
        Row(test_id="T1", emp_id="E1", order_date="2025-08-01 10:00:00", status="Completed"),
        Row(test_id="T2", emp_id="E2", order_date="2025-08-01 10:00:00", status="Completed"),
    ]
    lab = [
        Row(test_id="T1", result_id="R1", result_date="2025-08-03 10:00:00", result_status="Normal", result_value="5.0", units="mmol/L"),
        Row(test_id="T2", result_id="R2", result_date="2025-08-05 10:00:00", result_status="Abnormal", result_value="9.5", units="mmol/L"),
    ]
    emp = [
        Row(emp_id="E1", statecode="CA", city="San Francisco", supervisor="Manager1"),
        Row(emp_id="E2", statecode="TX", city="Dallas", supervisor="Manager2")
    ]

    facts = GoldProcessor.build_fact_test_orders(
        spark.createDataFrame(tests),
        spark.createDataFrame(lab),
        spark.createDataFrame(emp)
    ).collect()
    fact_dict = {r["test_id"]: r for r in facts}

    assert fact_dict["T1"]["tat_days"] == 2.0
    assert fact_dict["T1"]["is_abnormal"] == 0
    assert fact_dict["T1"]["followup_priority"] == "Low"

    assert fact_dict["T2"]["tat_days"] == 4.0
    assert fact_dict["T2"]["is_abnormal"] == 1
    assert fact_dict["T2"]["followup_priority"] == "High"