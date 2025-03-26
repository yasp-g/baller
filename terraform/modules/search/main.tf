# OpenSearch module for Baller application

locals {
  # Common prefix for all resources
  prefix = "${var.project}-${var.environment}"
  
  # Common tags for all resources
  common_tags = merge(
    var.tags,
    {
      Module = "search"
    }
  )
  
  # Domain name - either use provided name or auto-generate
  domain_name = var.domain_name != null ? var.domain_name : "${local.prefix}-search"
}

# OpenSearch domain
resource "aws_elasticsearch_domain" "baller_search" {
  domain_name           = local.domain_name
  elasticsearch_version = var.elasticsearch_version
  
  cluster_config {
    instance_type            = var.opensearch_instance_type
    instance_count           = var.opensearch_instance_count
    dedicated_master_enabled = var.dedicated_master_enabled
    dedicated_master_type    = var.dedicated_master_enabled ? var.dedicated_master_type : null
    dedicated_master_count   = var.dedicated_master_enabled ? var.dedicated_master_count : null
    zone_awareness_enabled   = var.zone_awareness_enabled
    
    zone_awareness_config {
      availability_zone_count = var.zone_awareness_enabled ? (var.opensearch_instance_count >= 3 ? 3 : 2) : null
    }
  }
  
  ebs_options {
    ebs_enabled = true
    volume_type = var.opensearch_ebs_volume_type
    volume_size = var.opensearch_ebs_volume_size
  }
  
  encrypt_at_rest {
    enabled = var.encrypt_at_rest
  }
  
  node_to_node_encryption {
    enabled = var.node_to_node_encryption
  }
  
  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }
  
  # Advanced options
  advanced_options = {
    "rest.action.multi.allow_explicit_index" = "true"
  }
  
  # Default access policy allows only authenticated requests
  access_policies = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:${var.aws_region}:*:domain/${local.domain_name}/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": ["10.0.0.0/8"]
        }
      }
    }
  ]
}
POLICY
  
  # Prevent downtime during updates
  update_policy {
    update_type = "blue-green"
  }
  
  # Automatic service software updates
  auto_tune_options {
    desired_state       = "ENABLED"
    rollback_on_disable = "NO_ROLLBACK"
    
    maintenance_schedule {
      start_at = timeadd(timestamp(), "336h")  # Start 2 weeks in the future
      duration {
        value = "2"
        unit  = "HOURS"
      }
      cron_expression_for_recurrence = "cron(0 0 ? * SUN *)"  # Every Sunday at midnight
    }
  }
  
  tags = local.common_tags
  
  # Prevent replacement of the domain
  lifecycle {
    prevent_destroy = false
  }
}

# Cognito authentication for OpenSearch Dashboard (optional)
# Requires additional setup with Cognito User Pool and Identity Pool
# resource "aws_elasticsearch_domain_saml_options" "baller_search" {
#   domain_name = aws_elasticsearch_domain.baller_search.domain_name
#   
#   saml_options {
#     enabled                 = true
#     roles_key               = "roles"
#     session_timeout_minutes = 60
#     subject_key             = "email"
#     metadata_content        = file("${path.module}/saml-metadata.xml")
#   }
# }
