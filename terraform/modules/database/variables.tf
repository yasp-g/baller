# Variables for the database module

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
# DynamoDB General Settings
###########################

variable "table_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "enable_encryption" {
  description = "Enable server-side encryption for DynamoDB tables"
  type        = bool
  default     = true
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for all tables"
  type        = bool
  default     = true
}

###########################
# Table-Specific Settings (used when PROVISIONED billing mode)
###########################

variable "conversations_table_read_capacity" {
  description = "Provisioned read capacity for conversations table"
  type        = number
  default     = 5
}

variable "conversations_table_write_capacity" {
  description = "Provisioned write capacity for conversations table"
  type        = number
  default     = 5
}

variable "messages_table_read_capacity" {
  description = "Provisioned read capacity for messages table"
  type        = number
  default     = 10
}

variable "messages_table_write_capacity" {
  description = "Provisioned write capacity for messages table"
  type        = number
  default     = 10
}

variable "preferences_table_read_capacity" {
  description = "Provisioned read capacity for preferences table"
  type        = number
  default     = 5
}

variable "preferences_table_write_capacity" {
  description = "Provisioned write capacity for preferences table"
  type        = number
  default     = 5
}

variable "api_interactions_table_read_capacity" {
  description = "Provisioned read capacity for API interactions table"
  type        = number
  default     = 5
}

variable "api_interactions_table_write_capacity" {
  description = "Provisioned write capacity for API interactions table"
  type        = number
  default     = 5
}

variable "llm_interactions_table_read_capacity" {
  description = "Provisioned read capacity for LLM interactions table"
  type        = number
  default     = 5
}

variable "llm_interactions_table_write_capacity" {
  description = "Provisioned write capacity for LLM interactions table"
  type        = number
  default     = 5
}

variable "feedback_table_read_capacity" {
  description = "Provisioned read capacity for feedback table"
  type        = number
  default     = 5
}

variable "feedback_table_write_capacity" {
  description = "Provisioned write capacity for feedback table"
  type        = number
  default     = 5
}

variable "entity_cache_table_read_capacity" {
  description = "Provisioned read capacity for entity cache table"
  type        = number
  default     = 5
}

variable "entity_cache_table_write_capacity" {
  description = "Provisioned write capacity for entity cache table"
  type        = number
  default     = 5
}

variable "metrics_table_read_capacity" {
  description = "Provisioned read capacity for metrics table"
  type        = number
  default     = 5
}

variable "metrics_table_write_capacity" {
  description = "Provisioned write capacity for metrics table"
  type        = number
  default     = 5
}

###########################
# TTL Configuration
###########################

variable "conversation_retention_days" {
  description = "Number of days to retain conversations before TTL deletion"
  type        = number
  default     = 30
}

variable "message_retention_days" {
  description = "Number of days to retain messages before TTL deletion"
  type        = number
  default     = 30
}

variable "api_interaction_retention_days" {
  description = "Number of days to retain API interaction data before TTL deletion"
  type        = number
  default     = 7
}

variable "llm_interaction_retention_days" {
  description = "Number of days to retain LLM interaction data before TTL deletion"
  type        = number
  default     = 7
}

variable "entity_cache_refresh_days" {
  description = "Number of days before entity cache entries need refreshing"
  type        = number
  default     = 7
}
