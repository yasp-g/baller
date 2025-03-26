# Outputs from the root Terraform module

# DynamoDB table names
output "dynamodb_conversations_table" {
  description = "Name of the DynamoDB conversations table"
  value       = module.database.conversations_table_name
}

output "dynamodb_messages_table" {
  description = "Name of the DynamoDB messages table"
  value       = module.database.messages_table_name
}

# S3 bucket names
output "s3_api_responses_bucket" {
  description = "Name of the S3 bucket for API responses"
  value       = module.storage.api_responses_bucket_name
}
