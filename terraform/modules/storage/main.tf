# S3 storage module

# API responses bucket
resource "aws_s3_bucket" "api_responses" {
  # Bucket configuration will go here
}

# LLM interactions bucket
resource "aws_s3_bucket" "llm_interactions" {
  # Bucket configuration will go here
}

# Message contexts bucket
resource "aws_s3_bucket" "message_contexts" {
  # Bucket configuration will go here
}
