from pyspark.sql import DataFrame
import pyspark.sql.functions as F

try:
    from src.glue.transformations import GenericTransformer
except ModuleNotFoundError:
    from transformations import GenericTransformer


class GoldProcessor:
    def __init__(self, config: dict):
        self.config = config

    @staticmethod
    def build_fact_test_orders(tests: DataFrame, lab: DataFrame, emp: DataFrame) -> DataFrame:
        lab_sub = lab.select("test_id", "result_id", "result_date", "result_status", "result_value", "units")
        emp_sub = emp.select("emp_id", "statecode", "city", "supervisor")

        joined = (
            tests.join(lab_sub, "test_id", "left")
            .join(emp_sub, "emp_id", "left")
            .withColumn("order_dt", F.to_date(F.col("order_date")))
            .withColumn("result_dt", F.to_date(F.col("result_date")))
            .withColumn(
                "tat_days",
                F.when(
                    F.col("result_date").isNotNull() & F.col("order_date").isNotNull(),
                    F.datediff(F.to_date(F.col("result_date")), F.to_date(F.col("order_date"))).cast("double")
                ).otherwise(F.lit(None))
            )
            .withColumn("is_abnormal", F.when(F.lower(F.col("result_status")) == "abnormal", 1).otherwise(0))
            .withColumn(
                "is_overdue",
                F.when(
                    (F.col("status").isin("Ordered", "In Progress")) &
                    (F.current_date() > F.date_add(F.col("order_dt"), 7)),
                    1
                ).otherwise(0)
            )
            .withColumn(
                "followup_priority",
                F.when(F.col("is_abnormal") == 1, "High")
                .when(F.col("is_overdue") == 1, "Medium")
                .otherwise("Low")
            )
        )
        return joined

    @staticmethod
    def build_daily_summary(fact_tests: DataFrame) -> DataFrame:
        return (
            fact_tests.groupBy("order_dt", "statecode")
            .agg(
                F.countDistinct("test_id").alias("total_tests"),
                F.sum(F.when(F.col("status") == "Completed", 1).otherwise(0)).alias("completed_tests"),
                F.round(F.avg("tat_days"), 2).alias("avg_tat_days"),
                F.sum("is_abnormal").alias("abnormal_results"),
                F.round(F.sum(F.when(F.col("status") == "Completed", 1).otherwise(0)) / F.countDistinct("test_id"), 4).alias("completion_rate")
            )
            .withColumnRenamed("order_dt", "report_date")
            .withColumn("processed_date", F.current_date())
        )

    @staticmethod
    def build_fhir(lab: DataFrame) -> DataFrame:
        return GenericTransformer.to_fhir_observation(lab)