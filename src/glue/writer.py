"""
writer.py: Production Data Lake Storage and Partition Optimization
Persists Silver, Gold, and Quarantine datasets to Amazon S3 in optimized Parquet.
"""

from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from utils import get_logger

logger = get_logger("WriterEngine")

class DataLakeWriter:
    def __init__(self, base_s3_path: str):
        self.base_s3_path = base_s3_path.rstrip("/")

    def write_dataset(
        self,
        df: DataFrame,
        entity_name: str,
        layer: str,
        partition_cols: list = None,
        target_partitions: int = 16,
        write_mode: str = "overwrite"
    ) -> str:
        """
        Writes DataFrame to S3 with partition tuning, snappy compression, and Parquet format.
        layer: 'silver' | 'gold' | 'quarantine'
        """
        target_path = f"{self.base_s3_path}/{layer}/{entity_name}"
        logger.info(f"Writing [{layer.upper()}] dataset '{entity_name}' to: {target_path}")

        writer = df

        # Partition Sizing Guard: avoid small-files problem
        if target_partitions > 0:
            if partition_cols:
                writer = writer.repartition(target_partitions, *partition_cols)
            else:
                writer = writer.coalesce(target_partitions)

        write_op = (
            writer.write
            .mode(write_mode)
            .format("parquet")
            .option("compression", "snappy")
        )

        if partition_cols:
            write_op = write_op.partitionBy(*partition_cols)

        write_op.save(target_path)
        logger.info(f"Successfully committed [{layer.upper()}] '{entity_name}'.")
        return target_path

    def write_quarantine(self, df: DataFrame, entity_name: str) -> str:
        """
        Persists rejected records with run metadata for auditability and MDM remediation.
        """
        if df.rdd.isEmpty():
            logger.info(f"Quarantine clean: No rejected records for {entity_name}.")
            return ""

        quarantine_df = df.withColumn("quarantine_ts", F.current_timestamp())
        return self.write_dataset(
            df=quarantine_df,
            entity_name=entity_name,
            layer="quarantine",
            partition_cols=None,
            target_partitions=1,
            write_mode="append"
        )