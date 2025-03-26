# Outputs from the storage module

output "api_responses_bucket_name" {
  description = "Name of the API responses bucket"
  value       = aws_s3_bucket.api_responses.bucket
}

output "llm_interactions_bucket_name" {
  description = "Name of the LLM interactions bucket"
  value       = aws_s3_bucket.llm_interactions.bucket
}

output "message_contexts_bucket_name" {
  description = "Name of the message contexts bucket"
  value       = aws_s3_bucket.message_contexts.bucket
}
