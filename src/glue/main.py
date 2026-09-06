import sys
import yaml
from pyspark.sql import SparkSession
from reader import ConfigDrivenReader
from silver import SilverProcessor
from gold import GoldProcessor
from writer import DataLakeWriter
from utils import get_logger

logger = get_logger("GlueMain")

def get_spark():
    try:
        from awsglue.utils import getResolvedOptions
        args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET_NAME', 'ENVIRONMENT', 'CONFIG_PATH'])
        spark = SparkSession.builder.getOrCreate()
        return spark, args
    except ImportError:
        spark = SparkSession.builder.master("local[*]").appName("EHS-Local").getOrCreate()
        return spark, {'S3_BUCKET_NAME': 'data', 'CONFIG_PATH': 'config/dev.yaml'}

def main():
    spark, args = get_spark()
    base_s3 = f"s3://{args['S3_BUCKET_NAME']}" if not args['S3_BUCKET_NAME'].startswith("data") else "./data"
    
    with open(args['CONFIG_PATH'], 'r') as f:
        config = yaml.safe_load(f)

    reader = ConfigDrivenReader(spark, args['CONFIG_PATH'], base_s3)
    silver = SilverProcessor(config)
    writer = DataLakeWriter(base_s3)

    # Ingestion & Silver
    emp_raw = reader.read("employee_master")
    tests_raw = reader.read("test_master")
    lab_raw = reader.read("lab_results")

    silver_emp, q_emp = silver.process("employee_master", emp_raw)
    silver_tests, q_tests = silver.process("test_master", tests_raw)
    silver_lab, q_lab = silver.process("lab_results", lab_raw)

    writer.write_dataset(silver_emp, "employee_master", "silver")
    writer.write_dataset(silver_tests, "test_master", "silver", partition_cols=["status"])
    writer.write_dataset(silver_lab, "lab_results", "silver")
    writer.write_quarantine(q_emp, "quarantine_emp")
    writer.write_quarantine(q_tests, "quarantine_tests")
    writer.write_quarantine(q_lab, "quarantine_lab")

    # Gold
    fact_tests = GoldProcessor.build_fact_test_orders(silver_tests, silver_lab, silver_emp)
    summary = GoldProcessor.build_daily_summary(fact_tests)
    fhir_obs = GoldProcessor.build_fhir(silver_lab)

    writer.write_dataset(fact_tests, "fact_test_order", "gold", partition_cols=["order_dt"])
    writer.write_dataset(summary, "health_summary_output", "gold", partition_cols=["report_date"])
    writer.write_dataset(fhir_obs, "fhir_observations", "gold")

    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()