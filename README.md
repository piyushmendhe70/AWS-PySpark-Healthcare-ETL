# Enterprise Healthcare ETL Pipeline (PySpark & AWS)

[![CI Pipeline](https://github.com/piyushmendhe70/AWS-PySpark-Healthcare-ETL/actions/workflows/ci.yml/badge.svg)](https://github.com/piyushmendhe70/AWS-PySpark-Healthcare-ETL/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Apache Spark](https://img.shields.io/badge/PySpark-3.5.1-orange.svg)](https://spark.apache.org/)
[![AWS Glue](https://img.shields.io/badge/AWS%20Glue-4.0%20(Serverless)-232F3E.svg)](https://aws.amazon.com/glue/)
[![Terraform 1.7+](https://img.shields.io/badge/Terraform-1.7%2B-7B42BC.svg)](https://www.terraform.io/)
[![HIPAA Compliance](https://img.shields.io/badge/Security-HIPAA%20Safe%20Harbor-green.svg)](#-security--hipaa-compliance)
[![FHIR Standard](https://img.shields.io/badge/Healthcare-HL7%20FHIR%20R4-firebrick.svg)](https://hl7.org/fhir/R4/)

An end-to-end, metadata-driven **Data Engineering & ETL Pipeline** deployed on AWS using PySpark and Terraform. Designed to handle enterprise-scale clinical data interoperability, this pipeline ingests heterogeneous healthcare messages (**HL7 v2, CCDA, ADT feeds**) and operational EHR extracts. It performs distributed transformations across a **Medallion Architecture (Bronze → Silver → Gold)** in Amazon S3, enforces **20+ automated Data Quality (DQ) validation gates**, and curates analytics-ready Star Schema marts alongside **HL7 FHIR R4** compliant observation resources.

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Key Engineering Capabilities](#-key-engineering-capabilities)
3. [Data Quality (DQ) & Quarantine Framework](#-data-quality-dq--quarantine-framework)
4. [Security & HIPAA Compliance](#-security--hipaa-compliance)
5. [Local Development & Testing](#-local-development--testing)
6. [CI/CD Automation](#-cicd-automation)
7. [Production Optimization & Incident Mitigations](#-production-optimization--incident-mitigations)
8. [Author & Contact](#-author--contact)

---

## 🏗 Architecture Overview

The platform uses an event-driven serverless workflow orchestrated by **AWS Step Functions**, decoupling initial file inspection from resource-intensive Spark workloads:

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                              UPSTREAM HEALTHCARE SYSTEMS                              │
 │   Hospital EHRs (Cerner/Epic) │ Third-Party Lab Networks │ MySQL EHS Operational DBs  │
 └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ Secure File Drops (SFTP / REST API)
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                      AWS EVENT-DRIVEN ORCHESTRATION PIPELINE                           │
 │                                                                                        │
 │   1. Ingestion Gate       2. Pre-Validation         3. State Orchestration             │
 │   ┌─────────────────┐     ┌──────────────────┐      ┌──────────────────────────────┐   │
 │   │ Amazon S3       │────▶│ AWS Lambda       │─────▶│ AWS Step Functions           │   │
 │   │ Bronze (Raw)    │     │ Ingestion Gate   │      │ • Choice State               │   │
 │   └─────────────────┘     └──────────────────┘      │ • Glue Synchronous Execution │   │
 │                                                     │ • SNS Alert Notifications    │   │
 │                                                     └──────────────┬───────────────┘   │
 └────────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                      │ Triggers (.sync)
                                                                      ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                         CORE PYSPARK PROCESSING (AWS GLUE 4.0)                         │
 │                                                                                        │
 │   BRONZE LAYER                 SILVER LAYER                     GOLD LAYER             │
 │   ┌────────────────────┐       ┌────────────────────────┐       ┌──────────────────┐   │
 │   │ Metadata Reader    │       │ Cleansing & Masking    │       │ Dimensional Marts│   │
 │   │ • Dynamic Schemas  │──────▶│ • Salted SHA-256 Mask  │──────▶│ • DimEmployee    │   │
 │   │ • config/dev.yaml  │       │ • Natural Key Dedup    │       │ • FactTestOrder  │   │
 │   │ • Permissive Catch │       │ • 20+ DQ Quality Gates │       │ • Health Summary │   │
 │   └────────────────────┘       └───────────┬────────────┘       │ • FHIR R4 Obs    │   │
 │                                            │                    └─────────┬────────┘   │
 │                                            ▼                              │            │
 │                                ┌────────────────────────┐                 │            │
 │                                │ S3 Quarantine Zone     │                 │            │
 │                                │ (Corrupt / Bad Feeds)  │                 │            │
 │                                └────────────────────────┘                 │            │
 └───────────────────────────────────────────────────────────────────────────┼────────────┘
                                                                             │
                                                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                CONSUMPTION & ANALYTICS                                 │
 │          Amazon Redshift / Athena          │      Executive Operational Dashboards     │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Engineering Capabilities

* Metadata-Driven Configuration: Externalized schemas, data types, business keys, and DQ validation parameters into config/dev.yaml, eliminating hardcoded column dependencies.
* Medallion Data Lake Architecture: Structured separation into Bronze (raw audit), Silver (cleansed, conformed, tokenized), and Gold (curated Star Schema and FHIR R4 resources).
* HIPAA Safe Harbor Compliance: Implemented automated SHA-256 salted tokenization and regex obfuscation for SSN, phone numbers, and corporate emails (transformations.py).
* Healthcare Interoperability (FHIR R4): Automated mapping of raw clinical lab observations into standard FHIR R4 JSON schemas (http://loinc.org and standard UCUM units).
* 20+ Automated Data Quality (DQ) Gates: Anti-join referential integrity validation, temporal sanity checks (future-date quarantine), status lifecycle reconciliation, and automated quarantine routing.
* Spark Performance & Skew Mitigation: Implemented two-phase salted aggregations to balance skewed provider keys and prevent executor OOMs; tuned partition sizing (~128MB) to eliminate the small-files problem.
* Infrastructure as Code (IaC): 100% automated AWS resource management using modular Terraform (S3, AWS Glue 4.0, Lambda, Step Functions, CodeBuild, IAM, and SNS).

## 🛡 Data Quality (DQ) & Quarantine Framework
The pipeline enforces strict data contracts at the Silver layer. Records failing validation are isolated into a quarantine S3 path with an appended quarantine_reason and quarantine_ts, ensuring bad data never halts downstream jobs.

Core Validations Implemented:

* Schema & Mandatory Fields: Fails fast if critical identifiers (emp_id, test_id) are missing or null.
* Temporal Integrity: Blocks future-dated clinical events (result_date > current_date()) and flags invalid date formats.
* Referential Integrity (Anti-Joins): Ensures all clinical tests and surveys link to a valid employee in the Employee Master.
* Lifecycle Coherence: Verifies that tests marked "Completed" have a corresponding lab result, and "Cancelled" tests do not.
* Deduplication: Applies survivorship rules to eliminate duplicate test_id or survey_id rows based on natural business keys.


## 🔒 Security & HIPAA Compliance
Data privacy is enforced before records land in the Silver layer to ensure downstream analytics environments remain free of exposed Protected Health Information (PHI).

* Salted Hashing: SSN, phone_number, and email fields are passed through a SHA-256 hash with a secure salt, allowing deterministic joins across tables without exposing the underlying identifier.
* Format Masking: Clear-text fields are obfuscated (e.g., ***-**-1234 or ***@hospital.org) for safe operational reporting.
* Encryption at Rest: All Amazon S3 buckets (Bronze, Silver, Gold, Quarantine) enforce AES-256 Server-Side Encryption (SSE-S3).


## 💻 Local Development & Testing
The pipeline supports local execution without deploying to AWS by falling back to a local PySpark session.

```bash
1. Clone and Setup
git clone https://github.com/piyushmendhe70/AWS-PySpark-Healthcare-ETL.git
cd AWS-PySpark-Healthcare-ETL
python -m venv venv
source venv/Scripts/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

2. Run PySpark Unit Tests
pytest tests/ -v --cov=src/glue --cov-report=term-missing

3. Run ETL Locally
python src/glue/main.py

```


## 🤖 CI/CD Automation
* GitHub Actions: Enforces PEP-8 code styling (flake8), runs local PySpark unit tests (pytest), and checks Terraform syntax on every pull request.

* AWS CodePipeline & CodeBuild: Modular Terraform configuration (infra/modules/cicd) provisions automated cloud build workflows using buildspec/buildspec.yaml to deploy code artifacts directly to S3.

🛠 Production Optimization & Incident Mitigations
* The "Small Files" Problem: Hourly clinical drops generate thousands of tiny files. The writer.py module utilizes .coalesce() and .repartition() based on the target_partitions parameter to ensure output Parquet files are optimally sized (~128MB) for Amazon Athena.

* Skewed Joins & Hot Keys: In healthcare, a few large hospital networks generate the majority of data. Joins use broadcast hints for smaller dimensions and salted keys (transformations.py) for heavy aggregations to prevent executor Out-Of-Memory (OOM) errors.

* Schema Evolution (Drift): Schemas are driven by config/dev.yaml rather than brittle inferSchema=True scans. Corrupt rows are isolated into quarantine via PySpark's _corrupt_record capture.

## 👨‍💻 Author & Contact
* Data Engineering Projects (PySpark, SQL, AWS)

* Email: mendhepiyush4@gmail.com

* GitHub: github.com/piyushmendhe70
