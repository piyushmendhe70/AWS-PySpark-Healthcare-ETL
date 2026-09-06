import logging
import sys
from typing import List, Tuple
from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def get_logger(name: str = "HealthcareETL") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class DataQualityGate:
    @staticmethod
    def enforce_temporal_integrity(df: DataFrame, date_cols: List[str]) -> Tuple[DataFrame, DataFrame]:
        if not date_cols:
            return df, df.limit(0)
        curr_dt = F.current_date()
        valid_cond = F.lit(True)
        for c in date_cols:
            valid_cond = valid_cond & (F.col(c).isNotNull() & (F.to_date(F.col(c)) <= curr_dt))
        return df.filter(valid_cond), df.filter(~valid_cond).withColumn("quarantine_reason", F.lit("TEMPORAL_VIOLATION"))

    @staticmethod
    def check_referential_integrity(child_df: DataFrame, parent_df: DataFrame, fk: str, pk: str) -> Tuple[DataFrame, DataFrame]:
        parent_keys = parent_df.select(pk).distinct()
        orphans = child_df.join(parent_keys, child_df[fk] == parent_keys[pk], "left_anti")
        valid = child_df.join(parent_keys, child_df[fk] == parent_keys[pk], "left_semi")
        return valid, orphans.withColumn("quarantine_reason", F.lit(f"ORPHAN_KEY_{fk}"))

    @staticmethod
    def check_lifecycle(tests_df: DataFrame, lab_df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        joined = tests_df.join(lab_df.select("test_id", F.col("result_date").alias("r_dt")), "test_id", "left")
        bad_completed = (F.lower(F.col("status")) == "completed") & F.col("r_dt").isNull()
        bad_cancelled = (F.lower(F.col("status")) == "cancelled") & F.col("r_dt").isNotNull()
        violation = bad_completed | bad_cancelled
        return joined.filter(~violation).drop("r_dt"), joined.filter(violation).withColumn("quarantine_reason", F.lit("LIFECYCLE_ERROR")).drop("r_dt")