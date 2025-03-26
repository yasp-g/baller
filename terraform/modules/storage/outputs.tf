# Outputs from the storage module

#############################
# API Responses Bucket
#############################

output "api_responses_bucket_name" {
  description = "Name of the API responses bucket"
  value       = aws_s3_bucket.api_responses.bucket
}

output "api_responses_bucket_arn" {
  description = "ARN of the API responses bucket"
  value       = aws_s3_bucket.api_responses.arn
}

output "api_responses_bucket_domain_name" {
  description = "Domain name of the API responses bucket"
  value       = aws_s3_bucket.api_responses.bucket_domain_name
}

#############################
# LLM Interactions Bucket
#############################

output "llm_interactions_bucket_name" {
  description = "Name of the LLM interactions bucket"
  value       = aws_s3_bucket.llm_interactions.bucket
}

output "llm_interactions_bucket_arn" {
  description = "ARN of the LLM interactions bucket"
  value       = aws_s3_bucket.llm_interactions.arn
}

output "llm_interactions_bucket_domain_name" {
  description = "Domain name of the LLM interactions bucket"
  value       = aws_s3_bucket.llm_interactions.bucket_domain_name
}

#############################
# Message Contexts Bucket
#############################

output "message_contexts_bucket_name" {
  description = "Name of the message contexts bucket"
  value       = aws_s3_bucket.message_contexts.bucket
}

output "message_contexts_bucket_arn" {
  description = "ARN of the message contexts bucket"
  value       = aws_s3_bucket.message_contexts.arn
}

output "message_contexts_bucket_domain_name" {
  description = "Domain name of the message contexts bucket"
  value       = aws_s3_bucket.message_contexts.bucket_domain_name
}

#############################
# All Buckets (for IAM policies)
#############################

output "all_bucket_arns" {
  description = "List of all bucket ARNs"
  value = [
    aws_s3_bucket.api_responses.arn,
    aws_s3_bucket.llm_interactions.arn,
    aws_s3_bucket.message_contexts.arn
  ]
}
