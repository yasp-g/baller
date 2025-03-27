# DynamoDB tables module for Baller application

locals {
  # Common prefix for all tables
  table_prefix = "${var.project}-${var.environment}"
  
  # Common tags for all resources
  common_tags = merge(
    var.tags,
    {
      Module = "database"
    }
  )
  
  # Check if using provisioned capacity
  is_provisioned = var.table_billing_mode == "PROVISIONED"
}

#############################
# Core Data Tables
#############################

# Conversations table
resource "aws_dynamodb_table" "conversations" {
  name         = "${local.table_prefix}-conversations"
  billing_mode = var.table_billing_mode
  hash_key     = "user_id"
  range_key    = "conversation_id"
  
  # Provisioned capacity settings (only used if billing_mode is PROVISIONED)
  read_capacity  = local.is_provisioned ? var.conversations_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.conversations_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "conversation_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "server_id"
    type = "S"
  }
  
  attribute {
    name = "created_at"
    type = "N"
  }
  
  attribute {
    name = "app_mode"
    type = "S"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "ServerIndex"
    hash_key           = "server_id"
    range_key          = "last_active"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.conversations_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.conversations_table_write_capacity : null
  }
  
  global_secondary_index {
    name               = "CreatedAtIndex"
    hash_key           = "app_mode"
    range_key          = "created_at"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.conversations_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.conversations_table_write_capacity : null
  }
  
  # Enable TTL
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

# Messages table
resource "aws_dynamodb_table" "messages" {
  name         = "${local.table_prefix}-messages"
  billing_mode = var.table_billing_mode
  hash_key     = "conversation_id"
  range_key    = "message_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.messages_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.messages_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "conversation_id"
    type = "S"
  }
  
  attribute {
    name = "message_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  attribute {
    name = "intent_name"
    type = "S"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "UserMessageIndex"
    hash_key           = "user_id"
    range_key          = "timestamp"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.messages_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.messages_table_write_capacity : null
  }
  
  global_secondary_index {
    name               = "IntentIndex"
    hash_key           = "intent_name"
    range_key          = "timestamp"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.messages_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.messages_table_write_capacity : null
  }
  
  # Enable TTL
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

# User preferences table
resource "aws_dynamodb_table" "preferences" {
  name         = "${local.table_prefix}-preferences"
  billing_mode = var.table_billing_mode
  hash_key     = "user_id"
  range_key    = "server_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.preferences_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.preferences_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "server_id"
    type = "S"
  }
  
  attribute {
    name = "last_updated"
    type = "N"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "ServerIndex"
    hash_key           = "server_id"
    range_key          = "last_updated"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.preferences_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.preferences_table_write_capacity : null
  }
  
  # No TTL for preferences as they should persist
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

#############################
# API & LLM Interaction Tables
#############################

# API interactions table
resource "aws_dynamodb_table" "api_interactions" {
  name         = "${local.table_prefix}-api-interactions"
  billing_mode = var.table_billing_mode
  hash_key     = "message_id"
  range_key    = "api_call_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.api_interactions_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.api_interactions_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "message_id"
    type = "S"
  }
  
  attribute {
    name = "api_call_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "endpoint"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "EndpointIndex"
    hash_key           = "endpoint"
    range_key          = "timestamp"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.api_interactions_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.api_interactions_table_write_capacity : null
  }
  
  # Enable TTL
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

# LLM interactions table
resource "aws_dynamodb_table" "llm_interactions" {
  name         = "${local.table_prefix}-llm-interactions"
  billing_mode = var.table_billing_mode
  hash_key     = "message_id"
  range_key    = "llm_call_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.llm_interactions_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.llm_interactions_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "message_id"
    type = "S"
  }
  
  attribute {
    name = "llm_call_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "provider"
    type = "S"
  }
  
  attribute {
    name = "model"
    type = "S"
  }
  
  attribute {
    name = "purpose"
    type = "S"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "ProviderModelIndex"
    hash_key           = "provider"
    range_key          = "model"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.llm_interactions_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.llm_interactions_table_write_capacity : null
  }
  
  global_secondary_index {
    name               = "PurposeIndex"
    hash_key           = "purpose"
    range_key          = "timestamp"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.llm_interactions_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.llm_interactions_table_write_capacity : null
  }
  
  # Enable TTL
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

#############################
# Analytics & Cache Tables
#############################

# Feedback table
resource "aws_dynamodb_table" "feedback" {
  name         = "${local.table_prefix}-feedback"
  billing_mode = var.table_billing_mode
  hash_key     = "message_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.feedback_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.feedback_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "message_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "rating_timestamp"
    type = "N"
  }
  
  attribute {
    name = "app_mode"
    type = "S"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "UserFeedbackIndex"
    hash_key           = "user_id"
    range_key          = "rating_timestamp"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.feedback_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.feedback_table_write_capacity : null
  }
  
  global_secondary_index {
    name               = "AppModeIndex"
    hash_key           = "app_mode"
    range_key          = "rating_timestamp"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.feedback_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.feedback_table_write_capacity : null
  }
  
  # No TTL for feedback as it's valuable long-term data
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

# Entity cache table
resource "aws_dynamodb_table" "entity_cache" {
  name         = "${local.table_prefix}-entity-cache"
  billing_mode = var.table_billing_mode
  hash_key     = "entity_type"
  range_key    = "entity_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.entity_cache_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.entity_cache_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "entity_type"
    type = "S"
  }
  
  attribute {
    name = "entity_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "normalized_name"
    type = "S"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "NameIndex"
    hash_key           = "normalized_name"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.entity_cache_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.entity_cache_table_write_capacity : null
  }
  
  # Enable TTL for cache refreshes
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}

# Metrics table
resource "aws_dynamodb_table" "metrics" {
  name         = "${local.table_prefix}-metrics"
  billing_mode = var.table_billing_mode
  hash_key     = "metric_date"
  range_key    = "metric_id"
  
  # Provisioned capacity settings
  read_capacity  = local.is_provisioned ? var.metrics_table_read_capacity : null
  write_capacity = local.is_provisioned ? var.metrics_table_write_capacity : null
  
  # Primary key attributes
  attribute {
    name = "metric_date"
    type = "S"
  }
  
  attribute {
    name = "metric_id"
    type = "S"
  }
  
  # GSI attributes
  attribute {
    name = "metric_category"
    type = "S"
  }
  
  attribute {
    name = "app_mode"
    type = "S"
  }
  
  # Global Secondary Indexes
  global_secondary_index {
    name               = "CategoryIndex"
    hash_key           = "metric_category"
    range_key          = "metric_date"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.metrics_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.metrics_table_write_capacity : null
  }
  
  global_secondary_index {
    name               = "AppModeIndex"
    hash_key           = "app_mode"
    range_key          = "metric_date"
    projection_type    = "ALL"
    read_capacity      = local.is_provisioned ? var.metrics_table_read_capacity : null
    write_capacity     = local.is_provisioned ? var.metrics_table_write_capacity : null
  }
  
  # No TTL for metrics as they're kept for historical analysis
  
  # Enable encryption
  server_side_encryption {
    enabled = var.enable_encryption
  }
  
  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }
  
  tags = local.common_tags
}
