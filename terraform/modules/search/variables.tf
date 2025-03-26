# Variables for the search module

###########################
# Core Variables (passed from root)
###########################

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project" {
  description = "Project name for resource naming"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

###########################
# OpenSearch Cluster Configuration
###########################

variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch nodes"
  type        = string
  default     = "t3.small.elasticsearch"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch nodes"
  type        = number
  default     = 1
}

variable "opensearch_ebs_volume_size" {
  description = "Size of EBS volumes attached to OpenSearch nodes (GB)"
  type        = number
  default     = 10
}

variable "opensearch_ebs_volume_type" {
  description = "Type of EBS volumes attached to OpenSearch nodes"
  type        = string
  default     = "gp3"
}

###########################
# OpenSearch Domain Settings
###########################

variable "domain_name" {
  description = "Name of the OpenSearch domain"
  type        = string
  default     = null # Will be auto-generated if not provided
}

variable "elasticsearch_version" {
  description = "Version of Elasticsearch/OpenSearch to deploy"
  type        = string
  default     = "OpenSearch_1.3"
}

variable "dedicated_master_enabled" {
  description = "Whether dedicated master nodes are enabled for the cluster"
  type        = bool
  default     = false
}

variable "dedicated_master_type" {
  description = "Instance type of the dedicated master nodes"
  type        = string
  default     = "t3.small.elasticsearch"
}

variable "dedicated_master_count" {
  description = "Number of dedicated master nodes"
  type        = number
  default     = 0
}

variable "zone_awareness_enabled" {
  description = "Whether zone awareness is enabled for the cluster"
  type        = bool
  default     = false
}

variable "encrypt_at_rest" {
  description = "Whether to enable encryption at rest"
  type        = bool
  default     = true
}

variable "node_to_node_encryption" {
  description = "Whether to enable node-to-node encryption"
  type        = bool
  default     = true
}
