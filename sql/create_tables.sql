-- Healthcare Claims Analytics Pipeline
-- Star Schema DDL
-- Project: CVS Health Data Engineer

-- Dimension: Patient
CREATE TABLE IF NOT EXISTS 
`healthcare-claims-cvs.healthcare_claims.dim_patient` (
    patient_id       STRING NOT NULL,
    state            STRING,
    discharge_status STRING,
    admission_type   STRING
);

-- Dimension: Provider
CREATE TABLE IF NOT EXISTS 
`healthcare-claims-cvs.healthcare_claims.dim_provider` (
    provider_id    STRING NOT NULL,
    provider_state STRING,
    npi_number     STRING
);

-- Dimension: Diagnosis
CREATE TABLE IF NOT EXISTS 
`healthcare-claims-cvs.healthcare_claims.dim_diagnosis` (
    diagnosis_code STRING NOT NULL,
    description    STRING
);

-- Fact: Claims
CREATE TABLE IF NOT EXISTS 
`healthcare-claims-cvs.healthcare_claims.fact_claims` (
    claim_id        STRING NOT NULL,
    patient_id      STRING,
    provider_id     STRING,
    diagnosis_code  STRING,
    claim_amount    FLOAT64,
    total_charges   FLOAT64,
    claim_from_date STRING,
    claim_thru_date STRING,
    drg_code        STRING
);