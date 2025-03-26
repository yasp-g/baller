# S3 storage module for Baller application

locals {
  # Common prefix for all buckets
  prefix = "${var.project}-${var.environment}"
  
  # Common tags for all resources
  common_tags = merge(
    var.tags,
    {
      Module = "storage"
    }
  )
  
  # Bucket names - either use provided names or auto-generate
  api_responses_bucket_name    = var.api_responses_bucket_name != null ? var.api_responses_bucket_name : "${local.prefix}-api-responses"
  llm_interactions_bucket_name = var.llm_interactions_bucket_name != null ? var.llm_interactions_bucket_name : "${local.prefix}-llm-interactions"
  message_contexts_bucket_name = var.message_contexts_bucket_name != null ? var.message_contexts_bucket_name : "${local.prefix}-message-contexts"
}

#############################
# API Responses Bucket
#############################

resource "aws_s3_bucket" "api_responses" {
  bucket = local.api_responses_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "api_responses" {
  bucket = aws_s3_bucket.api_responses.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "api_responses" {
  bucket = aws_s3_bucket.api_responses.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "api_responses" {
  bucket = aws_s3_bucket.api_responses.id
  
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "api_responses" {
  bucket = aws_s3_bucket.api_responses.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "api_responses" {
  bucket = aws_s3_bucket.api_responses.id
  
  rule {
    id      = "transition-and-expiration"
    status  = var.lifecycle_rules_enabled ? "Enabled" : "Disabled"
    
    transition {
      days          = var.standard_ia_transition_days
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = var.glacier_transition_days
      storage_class = "GLACIER"
    }
    
    expiration {
      days = var.expiration_days
    }
  }
}

#############################
# LLM Interactions Bucket
#############################

resource "aws_s3_bucket" "llm_interactions" {
  bucket = local.llm_interactions_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "llm_interactions" {
  bucket = aws_s3_bucket.llm_interactions.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "llm_interactions" {
  bucket = aws_s3_bucket.llm_interactions.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "llm_interactions" {
  bucket = aws_s3_bucket.llm_interactions.id
  
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "llm_interactions" {
  bucket = aws_s3_bucket.llm_interactions.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "llm_interactions" {
  bucket = aws_s3_bucket.llm_interactions.id
  
  rule {
    id      = "transition-and-expiration"
    status  = var.lifecycle_rules_enabled ? "Enabled" : "Disabled"
    
    transition {
      days          = var.standard_ia_transition_days
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = var.glacier_transition_days
      storage_class = "GLACIER"
    }
    
    expiration {
      days = var.expiration_days
    }
  }
}

#############################
# Message Contexts Bucket
#############################

resource "aws_s3_bucket" "message_contexts" {
  bucket = local.message_contexts_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_ownership_controls" "message_contexts" {
  bucket = aws_s3_bucket.message_contexts.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "message_contexts" {
  bucket = aws_s3_bucket.message_contexts.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "message_contexts" {
  bucket = aws_s3_bucket.message_contexts.id
  
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "message_contexts" {
  bucket = aws_s3_bucket.message_contexts.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "message_contexts" {
  bucket = aws_s3_bucket.message_contexts.id
  
  rule {
    id      = "transition-and-expiration"
    status  = var.lifecycle_rules_enabled ? "Enabled" : "Disabled"
    
    transition {
      days          = var.standard_ia_transition_days
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = var.glacier_transition_days
      storage_class = "GLACIER"
    }
    
    expiration {
      days = var.expiration_days
    }
  }
}
