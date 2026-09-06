import os
from pathlib import Path


def setup_project_structure():
    # Define the root path relative to where this script is executed
    root_dir = Path(__file__).resolve().parent

    print(f"🚀 Starting repository verification/scaffolding at: {root_dir}\n")

    # Define all directories that must exist
    directories = [
        ".github/workflows",
        "buildspec",
        "config",
        "docs",
        "src/glue",
        "src/lambda/check_s3_file",
        "stepfunctions",
        "infra/modules/s3",
        "infra/modules/glue",
        "infra/modules/lambda",
        "infra/modules/step_functions",
        "infra/modules/cicd",
        "infra/environments/dev",
        "tests",
    ]

    # Define all files that must exist (with default empty content or minimal templates)
    files = {
        ".github/workflows/ci.yml": "# Automated lint & test workflow\n",
        ".gitignore": "*.pyc\n__pycache__/\n.terraform/\n*.tfstate*\n",
        "README.md": "# AWS PySpark Healthcare ETL\nProduction-ready healthcare data pipeline.\n",
        "requirements.txt": "pyspark==3.4.1\npytest==7.4.0\npyyaml==6.0.1\n",
        "buildspec/buildspec.yaml": "# AWS CodeBuild / CodePipeline spec\nversion: 0.2\n",
        "config/dev.yaml": "# Master Schema, DQ contracts & Business parameters\n",
        "docs/data_dictionary.md": "# Data Dictionary\n",
        "src/glue/main.py": "# Entry point (reads config/dev.yaml, runs stages)\n",
        "src/glue/reader.py": "# Dynamic YAML schema builder & S3 reader\n",
        "src/glue/transformations.py": "# Business transformations, salting & FHIR mappings\n",
        "src/glue/silver.py": "# Silver execution: DQ/DV & quarantine segregation\n",
        "src/glue/gold.py": "# Gold execution: Star Schema, TAT & KPIs\n",
        "src/glue/utils.py": "# Core DQ helpers & minimal logging\n",
        "src/glue/writer.py": "# Optimized snappy Parquet writer with coalesce\n",
        "src/lambda/check_s3_file/lambda_function.py": "# File arrival pre-validation gate\ndef lambda_handler(event, context):\n    pass\n",
        "stepfunctions/etl_pipeline.asl.json": "{\n  \"Comment\": \"State Machine orchestration\"\n}\n",
        "infra/environments/dev/main.tf": "# Dev environment infrastructure entrypoint\n",
        "infra/environments/dev/variables.tf": "# Infrastructure variables\n",
        "infra/environments/dev/terraform.tfvars.example": "# Example variable values\n",
        "tests/conftest.py": "# PyTest configurations and shared fixtures\n",
        "tests/test_silver_dq.py": "# Test suite for Data Quality logic\n",
        "tests/test_gold_transforms.py": "# Test suite for analytical transformations\n",
    }

    # 1. Verify and create directories
    print("📁 Checking Directories...")
    for rel_dir in directories:
        target_dir = root_dir / rel_dir
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"  🆕 Created missing directory: {rel_dir}")
        else:
            print(f"  ✅ Directory already exists:  {rel_dir}")

    print("\n📄 Checking Files...")
    # 2. Verify and create files (Will NEVER overwrite existing data)
    for rel_file, default_content in files.items():
        target_file = root_dir / rel_file
        if not target_file.exists():
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(default_content)
            print(f"  🆕 Created missing file:      {rel_file}")
        else:
            print(f"  🔒 File already exists (kept): {rel_file}")

    print("\n🎯 Structure verification complete!")


if __name__ == "__main__":
    setup_project_structure()
