from typing import Tuple
from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from transformations import GenericTransformer
from utils import DataQualityGate

class SilverProcessor:
    def __init__(self, config: dict):
        self.config = config

    def process(self, entity: str, raw_df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        cfg = self.config["datasets"][entity]
        clean = raw_df.filter(F.col("_corrupt_record").isNull()).drop("_corrupt_record")
        corrupt = raw_df.filter(F.col("_corrupt_record").isNotNull()).withColumn("quarantine_reason", F.lit("CORRUPT_RECORD"))

        deduped = clean.dropDuplicates(cfg["business_keys"])
        masked = GenericTransformer.mask_phi(deduped, cfg["schema"], cfg["business_keys"][0])

        temporal_cols = cfg.get("dq_rules", {}).get("temporal_checks", [])
        valid, temporal_bad = DataQualityGate.enforce_temporal_integrity(masked, temporal_cols)

        return valid, corrupt.unionByName(temporal_bad, allowMissingColumns=True)