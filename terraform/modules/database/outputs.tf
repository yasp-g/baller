# Outputs from the database module

#############################
# Core Data Tables
#############################

output "conversations_table_name" {
  description = "Name of the conversations table"
  value       = aws_dynamodb_table.conversations.name
}

output "conversations_table_arn" {
  description = "ARN of the conversations table"
  value       = aws_dynamodb_table.conversations.arn
}

output "messages_table_name" {
  description = "Name of the messages table"
  value       = aws_dynamodb_table.messages.name
}

output "messages_table_arn" {
  description = "ARN of the messages table"
  value       = aws_dynamodb_table.messages.arn
}

output "preferences_table_name" {
  description = "Name of the preferences table"
  value       = aws_dynamodb_table.preferences.name
}

output "preferences_table_arn" {
  description = "ARN of the preferences table"
  value       = aws_dynamodb_table.preferences.arn
}

#############################
# API & LLM Interaction Tables
#############################

output "api_interactions_table_name" {
  description = "Name of the API interactions table"
  value       = aws_dynamodb_table.api_interactions.name
}

output "api_interactions_table_arn" {
  description = "ARN of the API interactions table"
  value       = aws_dynamodb_table.api_interactions.arn
}

output "llm_interactions_table_name" {
  description = "Name of the LLM interactions table"
  value       = aws_dynamodb_table.llm_interactions.name
}

output "llm_interactions_table_arn" {
  description = "ARN of the LLM interactions table"
  value       = aws_dynamodb_table.llm_interactions.arn
}

#############################
# Analytics & Cache Tables
#############################

output "feedback_table_name" {
  description = "Name of the feedback table"
  value       = aws_dynamodb_table.feedback.name
}

output "feedback_table_arn" {
  description = "ARN of the feedback table"
  value       = aws_dynamodb_table.feedback.arn
}

output "entity_cache_table_name" {
  description = "Name of the entity cache table"
  value       = aws_dynamodb_table.entity_cache.name
}

output "entity_cache_table_arn" {
  description = "ARN of the entity cache table"
  value       = aws_dynamodb_table.entity_cache.arn
}

output "metrics_table_name" {
  description = "Name of the metrics table"
  value       = aws_dynamodb_table.metrics.name
}

output "metrics_table_arn" {
  description = "ARN of the metrics table"
  value       = aws_dynamodb_table.metrics.arn
}

#############################
# All Tables (for IAM policies)
#############################

output "all_table_arns" {
  description = "List of all table ARNs"
  value = [
    aws_dynamodb_table.conversations.arn,
    aws_dynamodb_table.messages.arn,
    aws_dynamodb_table.preferences.arn,
    aws_dynamodb_table.api_interactions.arn,
    aws_dynamodb_table.llm_interactions.arn,
    aws_dynamodb_table.feedback.arn,
    aws_dynamodb_table.entity_cache.arn,
    aws_dynamodb_table.metrics.arn
  ]
}
