import yaml
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, IntegerType

TYPE_MAP = {
    "string": StringType(),
    "double": DoubleType(),
    "timestamp": TimestampType(),
    "integer": IntegerType()
}

class ConfigDrivenReader:
    def __init__(self, spark: SparkSession, config_path: str, base_path: str):
        self.spark = spark
        self.base_path = base_path.rstrip("/")
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def get_schema(self, entity: str) -> StructType:
        cfg = self.config["datasets"][entity]
        fields = [StructField(c["name"], TYPE_MAP.get(c["type"], StringType()), c.get("nullable", True)) for c in cfg["schema"]]
        fields.append(StructField("_corrupt_record", StringType(), True))
        return StructType(fields)

    def read(self, entity: str) -> DataFrame:
        cfg = self.config["datasets"][entity]
        schema = self.get_schema(entity)
        path = f"{self.base_path}/{cfg['raw_path']}/"
        return (
            self.spark.read.format(cfg.get("source_format", "csv"))
            .schema(schema)
            .option("header", "true")
            .option("mode", "PERMISSIVE")
            .option("columnNameOfCorruptRecord", "_corrupt_record")
            .load(path)
        )