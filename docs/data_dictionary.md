# Enterprise Healthcare Data Platform - Data Dictionary

## 1. Storage Layers (Medallion Architecture)
* **Bronze (`/bronze/`):** Raw HL7 v2 payloads, CSV/JSON drops stored as received for full auditability.
* **Silver (`/silver/`):** Cleaned, deduplicated, and HIPAA-tokenized entities.
* **Gold (`/gold/`):** Business-ready Star Schema facts, conformed dimensions, FHIR R4 resources, and KPI rollups.
* **Quarantine (`/quarantine/`):** Records failing Data Quality (DQ) gates with timestamps and error codes.

---

## 2. Target Data Models

### A. DimEmployee (`gold/dim_employee`)
| Field | Type | Description | Privacy / Security |
| :--- | :--- | :--- | :--- |
| `emp_id` | STRING | Unique Employee / Participant ID | Primary Key |
| `emp_name` | STRING | Cleaned Name (Title case) | Public |
| `masked_ssn` | STRING | Masked SSN (`***-**-1234`) | HIPAA Masked |
| `ssn_hash` | STRING | Salted SHA-256 Hash | Linkable Hash |
| `supervisor` | STRING | Supervisor Identifier | Plaintext |
| `employment_status` | STRING | Active / Inactive | Categorical |
| `city` | STRING | Cleaned City Name | Plaintext |
| `statecode` | STRING | 2-character State Code (ISO-2) | Partition Key |
| `masked_email` | STRING | Masked Email (`***@hospital.org`) | Obfuscated |
| `email_domain` | STRING | Corporate vs. Webmail domain | Analytics Feature |

### B. FactTestOrder (`gold/fact_test_order`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `test_id` | STRING | Primary Test Order Identifier |
| `emp_id` | STRING | Foreign Key -> DimEmployee |
| `order_date` | TIMESTAMP | Test Order Timestamp |
| `result_date` | TIMESTAMP | Clinical Result Availability Timestamp |
| `tat_days` | DOUBLE | Turnaround Time in Days (`result_date - order_date`) |
| `result_status` | STRING | Normal / Abnormal / Pending |
| `is_abnormal` | INT | Flag (1 if Abnormal, 0 otherwise) |
| `is_overdue` | INT | Flag (1 if uncompleted after 7 days) |
| `followup_priority` | STRING | High (Abnormal) / Medium (Overdue) / Low |

### C. FHIR R4 Observation (`gold/fhir_r4_observations`)
| Path | Type | Standard Reference |
| :--- | :--- | :--- |
| `resourceType` | STRING | `"Observation"` |
| `id` | STRING | Unique Result Identifier |
| `status` | STRING | `final` \| `preliminary` |
| `code.coding.system` | STRING | `http://loinc.org` |
| `subject.reference` | STRING | `Patient/{emp_id}` |
| `valueQuantity.value` | DOUBLE | Clinical Metric Value |
| `valueQuantity.unit` | STRING | Standardized Units (`http://unitsofmeasure.org`) |
| `interpretation` | STRING | Clinical Assessment (`Normal` / `Abnormal`) |