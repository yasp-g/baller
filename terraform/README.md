# Baller Infrastructure - Terraform

This directory contains the Terraform configuration for Baller's AWS infrastructure, including database resources, storage, and search capabilities.

## Directory Structure

```
/terraform/
  /modules/                # Reusable Terraform modules
    /database/             # DynamoDB tables configuration
    /storage/              # S3 buckets configuration
    /search/               # OpenSearch domain configuration
  /environments/           # Environment-specific configurations
    /dev/                  # Development environment
    /staging/              # Staging environment
    /prod/                 # Production environment
  main.tf                  # Main Terraform configuration
  variables.tf             # Variable definitions
  outputs.tf               # Output definitions
  README.md                # This file
```

## Modules

### Database Module

Creates and configures the DynamoDB tables as defined in the [Database Plan](/docs/DATABASE_PLAN.md):

- `baller-conversations` - Stores user conversation data
- `baller-messages` - Stores individual message data with processing metadata
- `baller-preferences` - Stores user preferences and settings
- `baller-api-interactions` - Tracks API calls
- `baller-llm-interactions` - Tracks LLM usage
- `baller-feedback` - Stores user feedback
- `baller-entity-cache` - Caches entity data
- `baller-metrics` - Stores application metrics

### Storage Module

Creates S3 buckets for storing larger objects:

- `baller-api-responses` - Stores complete API responses
- `baller-llm-interactions` - Stores complete LLM prompts and responses
- `baller-message-contexts` - Stores complete message context data

### Search Module

Configures Amazon OpenSearch Service for search and analytics:

- `baller-search` - OpenSearch domain for conversation and feedback analysis

## Environment-Specific Configuration

Each environment (dev, staging, prod) has its own configuration that references the root module with environment-specific variables.

## Usage

### Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) (v1.0.0+)
- AWS CLI configured with appropriate credentials
- Scalr account for state management

### Deploying to an Environment

#### 1. Navigate to the environment directory:

```bash
cd terraform/environments/dev
```

#### 2. Create your `state.config` file from the example:

```bash
cp ../../state.config.example state.config
# Edit state.config with your actual Scalr credentials
```

#### 3. Initialize Terraform:

```bash
terraform init -backend-config="state.config"
```

#### 4. Plan the deployment:

```bash
terraform plan
```

#### 5. Apply the changes:

```bash
terraform apply
```

### Destroying Resources

To destroy resources for an environment:

```bash
cd terraform/environments/dev
terraform destroy
```

## State Management

### Scalr as Backend

This project uses Scalr as the Terraform state backend. The configuration follows security best practices by using a partial configuration approach:

1. The `terraform { backend "remote" {} }` block contains minimal configuration in version control
2. Sensitive configuration is stored in a `state.config` file that is not committed to git
3. The backend is initialized with: `terraform init -backend-config="state.config"`

### Setting Up State Configuration

For each environment:

1. Copy the root `state.config.example` file to your environment directory:
   ```bash
   cd terraform/environments/dev
   cp ../../state.config.example state.config
   ```
2. Edit the state.config file with your actual Scalr credentials:
   ```hcl
   hostname     = "your-username.scalr.io"
   organization = "env-your-environment-id"
   workspaces   = { name = "baller-dev" }  # Use the appropriate environment name
   ```
3. Run Terraform initialization with this config file

### CI/CD Configuration

For CI/CD pipelines, use environment secrets to create the `state.config` file dynamically:

```yaml
# Example GitHub Actions step
- name: Create Terraform Backend Config
  run: |
    cat > state.config <<EOF
    hostname     = "${{ secrets.SCALR_HOSTNAME }}"
    organization = "${{ secrets.SCALR_ORGANIZATION }}"
    workspaces   = { name = "${{ secrets.SCALR_WORKSPACE }}" }
    EOF
    
- name: Terraform Init
  run: terraform init -backend-config="state.config"
```

## Tagging Strategy

All resources are tagged with:

- `Project`: "baller"
- `Environment`: "dev", "staging", or "prod"
- `ManagedBy`: "terraform"

## Security Considerations

- DynamoDB tables use encryption at rest
- S3 buckets enforce SSL and have appropriate access policies
- OpenSearch domains use VPC access and fine-grained access control
- Sensitive backend configuration is kept out of version control