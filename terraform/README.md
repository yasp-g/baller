# Baller Infrastructure - OpenTofu

This directory contains the OpenTofu configuration for Baller's AWS infrastructure, including database resources, storage, and search capabilities.

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
  variables.tf             # Global variable definitions
  outputs.tf               # Output definitions
  terraform.tfvars.example # Example variable values
  state.config.example     # Example backend configuration
  README.md                # This file
```

## Variable Management Structure

The OpenTofu configuration uses a hierarchical variable management approach:

```
terraform/
  variables.tf             # Global variables with defaults
  terraform.tfvars.example # Default values examples (gitignored)
  
  modules/
    database/
      variables.tf         # Database-specific variables
      
    storage/
      variables.tf         # Storage-specific variables
      
    search/
      variables.tf         # Search-specific variables
      
  environments/
    dev/
      main.tf              # Dev-specific module references
      terraform.tfvars.example # Dev-specific example values
    
    staging/
      main.tf              # Staging-specific module references
      terraform.tfvars.example # Staging-specific example values
      
    prod/
      main.tf              # Production-specific module references
      terraform.tfvars.example # Production-specific example values
```

### Variable Precedence

Variables follow this precedence (highest to lowest):
1. Environment-specific terraform.tfvars
2. Values explicitly set in environment's main.tf
3. Root terraform.tfvars
4. Default values in module's variables.tf
5. Default values in root variables.tf

## Modules

### Database Module

Creates and configures DynamoDB tables as defined in the [Database Plan](/docs/DATABASE_PLAN.md):

#### Core Data Tables
- `baller-conversations` - Stores user conversation data
  - Partition Key: `user_id`, Range Key: `conversation_id`
  - GSIs: `ServerIndex`, `CreatedAtIndex`
  - TTL-based expiry

- `baller-messages` - Stores individual message data
  - Partition Key: `conversation_id`, Range Key: `message_id`
  - GSIs: `UserMessageIndex`, `IntentIndex`
  - Tracks processing metadata and references to S3 objects

- `baller-preferences` - Stores user preferences and settings
  - Partition Key: `user_id`, Range Key: `server_id`
  - GSI: `ServerIndex`
  - Persistent storage (no TTL)

#### API & LLM Interaction Tables
- `baller-api-interactions` - Tracks API calls with metadata
  - Partition Key: `message_id`, Range Key: `api_call_id`
  - GSI: `EndpointIndex`
  - Links to S3 for complete response storage

- `baller-llm-interactions` - Tracks LLM usage and responses
  - Partition Key: `message_id`, Range Key: `llm_call_id`
  - GSIs: `ProviderModelIndex`, `PurposeIndex`
  - Performance metrics and token usage

#### Analytics & Cache Tables
- `baller-feedback` - Stores user feedback on responses
  - Partition Key: `message_id`
  - GSIs: `UserFeedbackIndex`, `AppModeIndex`
  - Persistent storage for long-term analysis

- `baller-entity-cache` - Caches entity data (teams, competitions)
  - Partition Key: `entity_type`, Range Key: `entity_id`
  - GSI: `NameIndex`
  - TTL-based refresh mechanism

- `baller-metrics` - Stores application performance metrics
  - Partition Key: `metric_date`, Range Key: `metric_id`
  - GSIs: `CategoryIndex`, `AppModeIndex`
  - Persistent storage for historical analysis

All tables include:
- Environment and project namespacing
- Server-side encryption
- Point-in-time recovery
- Consistent tagging
- Capacity scaling based on environment needs

### Storage Module

Creates S3 buckets with security best practices and lifecycle management:

- `baller-api-responses` - Stores complete API responses
  - Server-side encryption (AES-256)
  - Lifecycle rules for cost optimization:
    - Standard → IA (30 days)
    - IA → Glacier (90 days)
    - Expiration (365 days)
  - Public access blocked
  - Versioning for data protection

- `baller-llm-interactions` - Stores complete LLM interactions
  - Identical security and lifecycle configuration
  - Maintains full context of prompts and responses
  - Preserves token-level details for analysis

- `baller-message-contexts` - Stores complete message contexts
  - Identical security and lifecycle configuration
  - Stores data that would be too large for DynamoDB
  - Enables complete conversation reconstruction

### Search Module

Configures Amazon OpenSearch Service for sophisticated search and analytics:

- `baller-search` - OpenSearch domain with:
  - Size-appropriate instances based on environment
  - EBS storage with automatic scaling
  - Multi-AZ deployment in production
  - Encryption at rest and in transit
  - Automated maintenance windows
  - Blue/green deployment for zero-downtime updates
  - Kibana dashboard access for visualization

## Environment-Specific Configuration

Each environment (dev, staging, prod) has its own configuration that references the root module with environment-specific variables.

## Usage

### Prerequisites

- [OpenTofu](https://opentofu.org/docs/intro/install/) (v1.9.0+)
- AWS CLI configured with appropriate credentials
- S3 or other backend for state management (optional)

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

#### 3. Initialize OpenTofu:

```bash
tofu init -backend-config="state.config"
```

#### 4. Plan the deployment:

```bash
tofu plan
```

#### 5. Apply the changes:

```bash
tofu apply
```

### Destroying Resources

To destroy resources for an environment:

```bash
cd terraform/environments/dev
tofu destroy
```

## State Management

### Scalr as Backend

This project uses Scalr as the OpenTofu state backend. The configuration follows security best practices by using a partial configuration approach:

1. The `terraform { backend "remote" {} }` block contains minimal configuration in version control
2. Sensitive configuration is stored in a `state.config` file that is not committed to git
3. The backend is initialized with: `tofu init -backend-config="state.config"`

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
3. Run OpenTofu initialization with this config file

### CI/CD Configuration

For CI/CD pipelines, use environment secrets to create the `state.config` file dynamically:

```yaml
# Example GitHub Actions step
- name: Create OpenTofu Backend Config
  run: |
    cat > state.config <<EOF
    hostname     = "${{ secrets.SCALR_HOSTNAME }}"
    organization = "${{ secrets.SCALR_ORGANIZATION }}"
    workspaces   = { name = "${{ secrets.SCALR_WORKSPACE }}" }
    EOF
    
- name: OpenTofu Init
  run: tofu init -backend-config="state.config"
```

## AWS Free Tier Optimization

The development environment is configured to optimize for AWS Free Tier usage:

### DynamoDB Free Tier Optimizations
- `PROVISIONED` billing mode with low capacity units (maximum 5 per table)
- Disabled point-in-time recovery to reduce costs
- Reduced TTL retention periods to minimize storage
- Free tier includes 25 WCU and 25 RCU across all tables

### S3 Free Tier Optimizations
- Versioning disabled to reduce storage costs
- Aggressive lifecycle rules to transition to cheaper storage classes
- Free tier includes 5GB of Standard storage

### OpenSearch Optimizations
- Uses `t3.micro.elasticsearch` instances (smallest available)
- Minimum EBS volume size (8GB)
- Single node deployment
- Note: OpenSearch is not included in the free tier, but this is the most economical configuration

## Tagging Strategy

All resources are tagged with:

- `Project`: "baller"
- `Environment`: "dev", "staging", or "prod" 
- `ManagedBy`: "OpenTofu"

## Security Considerations

- DynamoDB tables use encryption at rest
- S3 buckets enforce SSL and have appropriate access policies
- OpenSearch domains use VPC access and fine-grained access control
- Sensitive backend configuration is kept out of version control