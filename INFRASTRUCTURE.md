# Infrastructure Setup

This document describes the AWS infrastructure setup for the Clinical Trial POC.

## AWS RDS PostgreSQL Database

### Database Details

| Property | Value |
|----------|-------|
| Instance Identifier | `clinical-trial-poc-db` |
| Engine | PostgreSQL 15 |
| Instance Class | db.t3.micro |
| Port | 5432 |
| Database Name | `clinicaltrials` |
| Region | us-west-2 |
| VPC | Default VPC |
| Publicly Accessible | Yes |

**Note:** Endpoint, username, and password should be stored securely and passed via environment variables.

### Security Group

| Property | Value |
|----------|-------|
| Name | `clinical-trial-db-sg` |
| Inbound Rule | TCP 5432 from 0.0.0.0/0 (POC only - restrict in production) |

**Note:** Note your Security Group ID after creation for use in RDS setup.

## Setup Steps

### 1. Create Security Group

```bash
aws ec2 create-security-group \
  --group-name clinical-trial-db-sg \
  --description "Security group for clinical trial POC database" \
  --vpc-id vpc-f20ac894
```

### 2. Add Inbound Rule for PostgreSQL

```bash
aws ec2 authorize-security-group-ingress \
  --group-id YOUR_SECURITY_GROUP_ID \
  --protocol tcp \
  --port 5432 \
  --cidr 0.0.0.0/0
```

### 3. Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier clinical-trial-poc-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --master-username YOUR_USERNAME \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids YOUR_SECURITY_GROUP_ID \
  --db-subnet-group-name default \
  --publicly-accessible \
  --db-name clinicaltrials \
  --backup-retention-period 0 \
  --no-multi-az
```

**Note:** Replace `YOUR_USERNAME`, `YOUR_SECURE_PASSWORD`, and `YOUR_SECURITY_GROUP_ID` with your values. Store credentials securely.

### 4. Wait for RDS to be Available

```bash
aws rds wait db-instance-available --db-instance-identifier clinical-trial-poc-db
```

### 5. Get RDS Endpoint

```bash
aws rds describe-db-instances \
  --db-instance-identifier clinical-trial-poc-db \
  --query 'DBInstances[0].Endpoint' \
  --output json
```

### 6. Populate Database

```bash
pip install psycopg2-binary

# Set environment variables
export DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
export DB_USER=your-db-username
export DB_PASSWORD=your-db-password

python setup_database.py
```

## Database Schema

### clinical_trials
| Column | Type | Description |
|--------|------|-------------|
| trial_id | VARCHAR(20) | Primary key (e.g., IMM-2024-001) |
| name | VARCHAR(200) | Trial name |
| phase | VARCHAR(10) | Phase 1, 2, or 3 |
| therapeutic_area | VARCHAR(100) | e.g., Immunology, Ophthalmology |
| start_date | DATE | Trial start date |
| status | VARCHAR(50) | Active, Recruiting, Completed |
| sponsor | VARCHAR(100) | Sponsoring company |

### patients
| Column | Type | Description |
|--------|------|-------------|
| patient_id | VARCHAR(20) | Primary key (e.g., PAT-00001) |
| trial_id | VARCHAR(20) | Foreign key to clinical_trials |
| age | INTEGER | Patient age |
| gender | VARCHAR(10) | Male/Female |
| treatment_arm | VARCHAR(50) | Treatment group assigned |
| enrollment_date | DATE | Date enrolled in trial |
| site_id | VARCHAR(20) | Clinical site identifier |

### adverse_events
| Column | Type | Description |
|--------|------|-------------|
| event_id | SERIAL | Primary key (auto-increment) |
| patient_id | VARCHAR(20) | Foreign key to patients |
| event_type | VARCHAR(100) | Type of adverse event |
| severity | VARCHAR(20) | Mild, Moderate, Severe |
| event_date | DATE | Date of event |
| resolved | BOOLEAN | Whether event was resolved |
| description | TEXT | Event description |

## Sample Data

The `setup_database.py` script populates the database with:

- **5 Clinical Trials** (Vision and Immunology focus)
  - IMM-2024-001: Uveitis Treatment Study
  - VIS-2023-042: Diabetic Retinopathy Prevention
  - IMM-2024-015: Rheumatoid Arthritis Biologic
  - VIS-2024-008: Age-Related Macular Degeneration
  - IMM-2023-089: Psoriasis IL-17 Inhibitor

- **~500 Patients** across all trials with randomized demographics

- **~150 Adverse Events** with appropriate event types per therapeutic area

## Cleanup

To delete the RDS instance and security group:

```bash
# Delete RDS instance
aws rds delete-db-instance \
  --db-instance-identifier clinical-trial-poc-db \
  --skip-final-snapshot

# Wait for deletion
aws rds wait db-instance-deleted --db-instance-identifier clinical-trial-poc-db

# Delete security group (replace with your security group ID)
aws ec2 delete-security-group --group-id YOUR_SECURITY_GROUP_ID
```

## Production Considerations

For production deployment, consider:

1. **Security**: Restrict security group to specific IP ranges or VPC
2. **Encryption**: Enable storage encryption
3. **Backups**: Enable automated backups
4. **Multi-AZ**: Enable for high availability
5. **Credentials**: Use AWS Secrets Manager instead of hardcoded passwords
6. **VPC**: Place RDS in private subnet with VPC peering to Domino
