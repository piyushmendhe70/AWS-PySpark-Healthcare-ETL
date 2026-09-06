from typing import List
from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType

class GenericTransformer:
    @staticmethod
    def mask_phi(df: DataFrame, schema_cfg: List[dict], id_col: str, salt: str = "EHS_2026") -> DataFrame:
        out = df
        for col_def in schema_cfg:
            col_name = col_def["name"]
            if col_def.get("phi_mask", False) and col_name in out.columns:
                out = (
                    out.withColumn(f"masked_{col_name}", F.concat(F.lit("***-"), F.substring(F.col(col_name), -4, 4)))
                    .withColumn(f"{col_name}_hash", F.sha2(F.concat_ws("::", F.col(id_col), F.col(col_name), F.lit(salt)), 256))
                    .drop(col_name)
                )
        return out

    @staticmethod
    def salted_aggregation(df: DataFrame, group_key: str, metric_col: str, salt_buckets: int = 16) -> DataFrame:
        salted = df.withColumn("salt", F.floor(F.rand() * salt_buckets))
        part = salted.groupBy(group_key, "salt").agg(F.count(metric_col).alias("p_count"), F.sum(metric_col).alias("p_sum"))
        return part.groupBy(group_key).agg(F.sum("p_count").alias(f"{metric_col}_count"), F.sum("p_sum").alias(f"{metric_col}_sum"))

    @staticmethod
    def to_fhir_observation(lab_df: DataFrame) -> DataFrame:
        return lab_df.select(
            F.lit("Observation").alias("resourceType"),
            F.col("result_id").alias("id"),
            F.when(F.lower(F.col("result_status")).isin("normal", "abnormal"), "final").otherwise("preliminary").alias("status"),
            F.struct(
                F.struct(
                    F.lit("http://loinc.org").alias("system"),
                    F.coalesce(F.col("loinc_code"), F.lit("UNK")).alias("code"),
                    F.col("test_name").alias("display")
                ).alias("coding"),
                F.col("test_name").alias("text")
            ).alias("code"),
            F.struct(F.concat(F.lit("Patient/"), F.col("emp_id")).alias("reference")).alias("subject"),
            F.col("result_date").alias("effectiveDateTime"),
            F.struct(
                F.col("result_value").cast(DoubleType()).alias("value"),
                F.coalesce(F.col("units"), F.lit("unit")).alias("unit"),
                F.lit("http://unitsofmeasure.org").alias("system")
            ).alias("valueQuantity"),
            F.col("result_status").alias("interpretation")
        )