# Variables for the storage module

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project" {
  description = "Project name for resource naming"
  type        = string
}

variable "lifecycle_rules_enabled" {
  description = "Whether to enable lifecycle rules for S3 buckets"
  type        = bool
  default     = true
}
