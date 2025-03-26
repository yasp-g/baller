# Variables for the root Terraform module

###########################
# Core Infrastructure Variables
###########################

# Environment
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

# AWS region
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-central-1"
}

# Project name
variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "baller"
}

###########################
# Global Tags
###########################

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

###########################
# DynamoDB Globals
###########################

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_enable_encryption" {
  description = "Enable server-side encryption for DynamoDB tables"
  type        = bool
  default     = true
}

variable "dynamodb_enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB tables"
  type        = bool
  default     = true
}

###########################
# S3 Globals
###########################

variable "s3_versioning_enabled" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_lifecycle_rules_enabled" {
  description = "Enable lifecycle rules for S3 buckets"
  type        = bool
  default     = true
}

variable "s3_standard_ia_transition_days" {
  description = "Days before transitioning objects to STANDARD_IA storage"
  type        = number
  default     = 30
}

variable "s3_glacier_transition_days" {
  description = "Days before transitioning objects to GLACIER storage"
  type        = number
  default     = 90
}

variable "s3_expiration_days" {
  description = "Days before expiring objects"
  type        = number
  default     = 365
}

###########################
# OpenSearch Globals
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
