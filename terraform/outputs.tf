# Outputs from the root Terraform module

###########################
# Core Information
###########################

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region used for resources"
  value       = var.aws_region
}

###########################
# DynamoDB Tables
###########################

output "dynamodb_conversations_table" {
  description = "Name of the DynamoDB conversations table"
  value       = module.database.conversations_table_name
}

output "dynamodb_messages_table" {
  description = "Name of the DynamoDB messages table"
  value       = module.database.messages_table_name
}

output "dynamodb_preferences_table" {
  description = "Name of the DynamoDB preferences table"
  value       = module.database.preferences_table_name
}

output "dynamodb_api_interactions_table" {
  description = "Name of the DynamoDB API interactions table"
  value       = module.database.api_interactions_table_name
}

output "dynamodb_llm_interactions_table" {
  description = "Name of the DynamoDB LLM interactions table"
  value       = module.database.llm_interactions_table_name
}

output "dynamodb_feedback_table" {
  description = "Name of the DynamoDB feedback table"
  value       = module.database.feedback_table_name
}

output "dynamodb_entity_cache_table" {
  description = "Name of the DynamoDB entity cache table"
  value       = module.database.entity_cache_table_name
}

output "dynamodb_metrics_table" {
  description = "Name of the DynamoDB metrics table"
  value       = module.database.metrics_table_name
}

###########################
# S3 Buckets
###########################

output "s3_api_responses_bucket" {
  description = "Name of the S3 bucket for API responses"
  value       = module.storage.api_responses_bucket_name
}

output "s3_llm_interactions_bucket" {
  description = "Name of the S3 bucket for LLM interactions"
  value       = module.storage.llm_interactions_bucket_name
}

output "s3_message_contexts_bucket" {
  description = "Name of the S3 bucket for message contexts"
  value       = module.storage.message_contexts_bucket_name
}

###########################
# OpenSearch
###########################

output "opensearch_endpoint" {
  description = "Endpoint for the OpenSearch domain"
  value       = module.search.opensearch_endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "Dashboard endpoint for the OpenSearch domain"
  value       = module.search.opensearch_dashboard_endpoint
}
