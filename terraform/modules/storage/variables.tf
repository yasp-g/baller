# Variables for the storage module

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
# S3 General Settings
###########################

variable "versioning_enabled" {
  description = "Enable versioning for S3 buckets"
  type        = bool
  default     = true
}

variable "encryption_enabled" {
  description = "Enable server-side encryption for S3 buckets"
  type        = bool
  default     = true
}

variable "lifecycle_rules_enabled" {
  description = "Whether to enable lifecycle rules for S3 buckets"
  type        = bool
  default     = true
}

###########################
# Lifecycle Configuration
###########################

variable "standard_ia_transition_days" {
  description = "Days before transitioning objects to STANDARD_IA storage"
  type        = number
  default     = 30
}

variable "glacier_transition_days" {
  description = "Days before transitioning objects to GLACIER storage"
  type        = number
  default     = 90
}

variable "expiration_days" {
  description = "Days before expiring objects"
  type        = number
  default     = 365
}

###########################
# Bucket-Specific Settings
###########################

variable "api_responses_bucket_name" {
  description = "Name of the S3 bucket for API responses"
  type        = string
  default     = null # Will be auto-generated if not provided
}

variable "llm_interactions_bucket_name" {
  description = "Name of the S3 bucket for LLM interactions"
  type        = string
  default     = null # Will be auto-generated if not provided
}

variable "message_contexts_bucket_name" {
  description = "Name of the S3 bucket for message contexts"
  type        = string
  default     = null # Will be auto-generated if not provided
}
