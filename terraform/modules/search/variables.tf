# Variables for the search module

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project" {
  description = "Project name for resource naming"
  type        = string
}

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
