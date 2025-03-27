# Baller Database Plan

## Overview

This database plan outlines a comprehensive storage strategy for the Baller application to track and store the full user message pipeline, from request to response, including all intermediate data processing steps and metrics.

## Goals

1. Durably store user-related data including preferences, conversation history, and feedback
2. Track the complete pipeline of message processing from input to output
3. Store API interaction data for analysis and improvement
4. Support analytics and debugging by capturing metrics at each processing step
5. Maintain data in a way that's easily queryable for analysis and reporting

## Database Systems

We'll use a combination of technologies to optimize for different data characteristics:

### 1. Amazon DynamoDB (Primary Database)

**Purpose:** Main NoSQL database for structured data storage with high availability requirements

**Characteristics:**
- Fully managed NoSQL database with single-digit millisecond performance
- Scales automatically to handle growth in users and messages
- Multi-region availability for high reliability 
- Supports time-to-live (TTL) for automatic data expiration
- Flexible schema for evolving data requirements

### 2. Amazon S3 (Blob Storage)

**Purpose:** Store larger objects like complete API responses, raw football data, and detailed LLM responses

**Characteristics:**
- Cost-effective storage for large objects
- 11 9's of durability for long-term storage
- Lifecycle policies for automatic archiving or deletion
- Ability to store complete context that's too large for DynamoDB

### 3. Amazon OpenSearch Service (Search/Analytics)

**Purpose:** Enable fast searching, filtering, and analysis of conversation and content data

**Characteristics:**
- Full-text search for finding specific conversations or terms
- Real-time analytics dashboards
- Visualization of user interaction patterns
- Complex query capabilities for data analysis

## Database Schema

### DynamoDB Schema

#### 1. Conversation Table

**Table Name:** `baller-conversations`
**Partition Key:** `user_id` (String)
**Range Key:** `conversation_id` (String)

**Key Design Justification:**
Using `user_id` as the PK rather than `server_id` is optimal because:
1. Most queries will be user-centric (retrieving user's conversation history)
2. User data is more evenly distributed than server data (some servers may have vastly more conversations than others)
3. This design provides better horizontal scaling as users are added
4. Server-specific queries are handled by the ServerIndex GSI
5. Most importantly, conversations typically span multiple messages and are continuous with a single user, making user_id the natural access pattern

**Attributes:**
- `user_id` (String): Discord user ID
- `conversation_id` (String): Unique conversation identifier
- `server_id` (String): Discord server ID where conversation occurred
- `created_at` (Number): Timestamp when conversation started
- `last_active` (Number): Timestamp of last message in conversation
- `ttl` (Number): Expiration timestamp for automatic deletion
- `app_mode` (String): Application mode (development, beta, production)
- `environment` (String): Environment (development, production)
- `messages` (List): Array of conversation messages (limited to most recent)
- `summary` (String): AI-generated summary of conversation (for longer conversations)
- `metrics` (Map):
  - `message_count` (Number): Total messages in conversation
  - `average_response_time` (Number): Average bot response time
  - `error_count` (Number): Errors encountered during conversation

**Global Secondary Indexes:**
1. `ServerIndex` - PK: `server_id`, SK: `last_active` (for server-specific queries)
2. `CreatedAtIndex` - PK: `app_mode`, SK: `created_at` (for time-based analytics)

#### 2. Message Table

**Table Name:** `baller-messages`
**Partition Key:** `conversation_id` (String)
**Range Key:** `message_id` (String)

**Attributes:**
- `conversation_id` (String): Link to parent conversation
- `message_id` (String): Unique message identifier
- `user_id` (String): Discord user ID
- `server_id` (String): Discord server ID
- `message_type` (String): "user" or "assistant"
- `content` (String): Message content
- `timestamp` (Number): Message creation timestamp
- `ttl` (Number): Expiration timestamp
- `relevance_check` (Map):
  - `is_relevant` (Boolean): Whether message was judged relevant
  - `confidence` (Number): Confidence score of relevance check
  - `explanation` (String): Explanation of relevance determination
  - `raw_response` (String): Full LLM relevance check response
- `intent` (Map):
  - `name` (String): Detected intent name
  - `confidence` (Number): Intent detection confidence score
  - `api_resource` (String): Associated API resource URI
  - `api_params` (Map): Parameters for API call
- `entities` (List): Extracted entities with IDs and confidence scores
- `context_used` (Boolean): Whether conversation context was used
- `s3_references` (Map): References to S3 objects (for large data)
- `processing_metadata` (Map):
  - `processing_time` (Number): Total processing time in ms
  - `relevance_check_time` (Number): Time for relevance check in ms
  - `intent_detection_time` (Number): Time for intent detection in ms
  - `api_call_time` (Number): Time for API call in ms
  - `llm_generation_time` (Number): Time for LLM response generation in ms

**Global Secondary Indexes:**
1. `UserMessageIndex` - PK: `user_id`, SK: `timestamp` (for user history)
2. `IntentIndex` - PK: `intent.name`, SK: `timestamp` (for intent-based analysis)

#### 3. User Preferences Table

**Table Name:** `baller-preferences`
**Partition Key:** `user_id` (String)
**Range Key:** `server_id` (String)

**Key Design Justification:**
Using `user_id` as PK and `server_id` as SK is optimal because:
1. User preferences should be server-specific (users may follow different teams on different servers)
2. This supports both per-server preferences and global user settings
3. Most queries will retrieve preferences for a specific user on a specific server
4. The composite key allows retrieving all preferences for a user across all servers in one query
5. Adding a GSI with server_id as PK allows for server-wide operations when needed

**Attributes:**
- `user_id` (String): Discord user ID
- `server_id` (String): Discord server ID
- `username` (String): Discord username (for reference)
- `followed_teams` (List): Teams followed by user
- `preferred_leagues` (List): Leagues preferred by user
- `notification_settings` (Map):
  - `game_reminders` (Boolean): Send game reminders
  - `score_updates` (Boolean): Send score updates
- `last_updated` (Number): Last update timestamp
- `created_at` (Number): Creation timestamp
- `preferences_version` (Number): Version for tracking schema changes

**Global Secondary Indexes:**
1. `ServerIndex` - PK: `server_id`, SK: `last_updated` (for server-wide operations)

#### 4. API Interactions Table

**Table Name:** `baller-api-interactions`
**Partition Key:** `message_id` (String)
**Range Key:** `api_call_id` (String)

**Attributes:**
- `message_id` (String): Associated message identifier
- `api_call_id` (String): Unique API call identifier
- `endpoint` (String): API endpoint called
- `parameters` (Map): Parameters sent to API
- `status_code` (Number): HTTP status code
- `success` (Boolean): Whether call succeeded
- `error_message` (String): Error message if any
- `response_size` (Number): Size of response in bytes
- `latency` (Number): API call latency in ms
- `timestamp` (Number): When call was made
- `ttl` (Number): Expiration timestamp
- `s3_reference` (String): S3 path to full response (if large)

**Global Secondary Indexes:**
1. `EndpointIndex` - PK: `endpoint`, SK: `timestamp` (for endpoint performance analysis)

#### 5. LLM Interactions Table

**Table Name:** `baller-llm-interactions`
**Partition Key:** `message_id` (String)
**Range Key:** `llm_call_id` (String)

**Attributes:**
- `message_id` (String): Associated message identifier
- `llm_call_id` (String): Unique LLM call identifier
- `provider` (String): LLM provider (Deepseek, Anthropic, etc.)
- `model` (String): Model used
- `purpose` (String): Why LLM was called (main_response, relevance_check, evaluation)
- `prompt_tokens` (Number): Tokens in prompt
- `completion_tokens` (Number): Tokens in completion
- `total_tokens` (Number): Total tokens used
- `latency` (Number): Generation time in ms
- `success` (Boolean): Whether call succeeded
- `error_message` (String): Error message if any
- `timestamp` (Number): When call was made
- `ttl` (Number): Expiration timestamp
- `s3_reference` (String): S3 path to full prompt and response

**Global Secondary Indexes:**
1. `ProviderModelIndex` - PK: `provider`, SK: `model` (for provider/model analysis)
2. `PurposeIndex` - PK: `purpose`, SK: `timestamp` (for purpose-based queries)

#### 6. Feedback Table

**Table Name:** `baller-feedback`
**Partition Key:** `message_id` (String)

**Attributes:**
- `message_id` (String): Message that received feedback
- `user_id` (String): User who gave feedback
- `rating` (String): "positive" or "negative"
- `rating_timestamp` (Number): When feedback was provided
- `follow_up_feedback` (String): Optional detailed feedback
- `app_mode` (String): Application mode when feedback was given
- `server_id` (String): Server where feedback was given
- `response_snapshot` (String): Content of the response at time of feedback
- `ttl` (Number): Optional expiration timestamp

**Global Secondary Indexes:**
1. `UserFeedbackIndex` - PK: `user_id`, SK: `rating_timestamp` (user's feedback history)
2. `AppModeIndex` - PK: `app_mode`, SK: `rating_timestamp` (feedback by app mode)

#### 7. Entity Cache Table

**Table Name:** `baller-entity-cache`
**Partition Key:** `entity_type` (String)
**Range Key:** `entity_id` (String)

**Attributes:**
- `entity_type` (String): Type of entity (team, competition, player)
- `entity_id` (String): Unique entity identifier
- `name` (String): Entity name
- `normalized_name` (String): Normalized name for matching
- `aliases` (List): Alternative names/spellings
- `metadata` (Map): Entity-specific metadata
- `last_updated` (Number): When entity was last updated
- `ttl` (Number): Expiration timestamp for refresh

**Global Secondary Indexes:**
1. `NameIndex` - PK: `normalized_name` (for name-based lookups)

#### 8. Metrics Table

**Table Name:** `baller-metrics`
**Partition Key:** `metric_date` (String) - YYYY-MM-DD
**Range Key:** `metric_id` (String) - category:name

**Attributes:**
- `metric_date` (String): Date of metric
- `metric_id` (String): Unique metric identifier
- `metric_category` (String): Category (latency, relevance, etc.)
- `metric_name` (String): Specific metric name
- `app_mode` (String): Application mode
- `values` (List): Array of recorded values
- `count` (Number): Count of data points
- `min` (Number): Minimum value
- `max` (Number): Maximum value
- `avg` (Number): Average value
- `p50` (Number): 50th percentile (median)
- `p90` (Number): 90th percentile
- `p99` (Number): 99th percentile

**Global Secondary Indexes:**
1. `CategoryIndex` - PK: `metric_category`, SK: `metric_date` (for category-based analysis)
2. `AppModeIndex` - PK: `app_mode`, SK: `metric_date` (for app mode comparisons)

### S3 Storage

#### 1. API Response Bucket

**Bucket Name:** `baller-api-responses`
**Path Format:** `/{year}/{month}/{day}/{conversation_id}/{message_id}/{api_call_id}.json`

Stores complete API responses that are too large for DynamoDB. References from API Interactions table.

#### 2. LLM Interactions Bucket

**Bucket Name:** `baller-llm-interactions`
**Path Format:** `/{year}/{month}/{day}/{conversation_id}/{message_id}/{llm_call_id}.json`

Stores complete prompt templates, prompts, and responses from LLM calls. Contains:
- Full prompt context
- Complete LLM responses
- Any additional metadata too large for DynamoDB

#### 3. Message Context Bucket

**Bucket Name:** `baller-message-contexts`
**Path Format:** `/{year}/{month}/{day}/{conversation_id}/{message_id}/context.json`

Stores complete context for message processing:
- Full conversation history used
- Complete user preferences
- Entity extraction details
- Other contextual information

### OpenSearch Schema

#### 1. Conversations Index

**Index Name:** `baller-conversations`

**Fields:**
- All fields from Conversations table
- Full-text search on message content
- Normalized entity names and values
- Analytics on conversation patterns
- Time-series data on usage

#### 2. Feedback Analytics Index

**Index Name:** `baller-feedback-analytics`

**Fields:**
- All fields from Feedback table
- Associated conversation and message metadata
- Term frequency for content analysis
- Sentiment analysis results
- User satisfaction metrics

## Data Flow

1. **Message Processing Pipeline**
   - User message received → Store in Messages table
   - Relevance check performed → Update Messages table with relevance data
   - Intent detection → Update Messages table with intent and entity data
   - API call made → Store in API Interactions table, large responses in S3
   - LLM response generated → Store in LLM Interactions table, large context in S3
   - Bot response sent → Update Messages table with response data
   - Feedback received → Store in Feedback table

2. **Analytics Pipeline**
   - Metrics aggregated daily → Store in Metrics table
   - Import relevant data to OpenSearch for analytics
   - Generate reports and dashboards for system performance

## Automatic Data Lifecycle

1. **Retention Policy**
   - Conversations: 30-day TTL by default (configurable)
   - API Responses: 7-day retention in DynamoDB, 30 days in S3
   - LLM Interactions: 7-day retention in DynamoDB, 30 days in S3
   - Feedback: No automatic expiration (valuable for long-term analysis)
   - Entity Cache: Refresh TTL based on entity type (teams: 7 days, competitions: 1 day)

2. **Archival Strategy**
   - Daily data export to S3 for long-term storage
   - Monthly aggregation of metrics with indefinite retention
   - Quarterly purge of personal identifiable information (PII) for inactive users

## Implementation Considerations

1. **AWS Infrastructure Requirements**
   - DynamoDB tables with appropriate provisioned capacity
   - S3 buckets with appropriate lifecycle policies
   - OpenSearch domains sized for expected query volume
   - IAM roles and policies for secure access

2. **Application Changes**
   - Update existing placeholder methods in ConversationManager and UserPreferencesManager
   - Add metadata collection at each processing step
   - Create data access layer for database interactions
   - Implement S3 storage for large objects
   - Add OpenSearch integration for analytics

3. **Cost Considerations**
   - Use DynamoDB on-demand capacity for unpredictable workloads
   - Implement S3 lifecycle policies to transition to lower-cost storage tiers
   - Monitor OpenSearch usage and scale appropriately
   - Consider reserved capacity for predictable workloads

## Future Extensions

1. **Real-time Analytics**
   - Stream data to Kinesis for real-time dashboards
   - Implement CloudWatch alarms for performance anomalies

2. **Machine Learning Pipeline**
   - Use SageMaker to analyze user patterns and improve responses
   - Implement automatic prompt optimization based on feedback

3. **Enhanced Privacy Controls**
   - Add user-configurable data retention policies
   - Implement fine-grained data masking for sensitive information

4. **Multi-Region Deployment**
   - Global tables for worldwide availability
   - Cross-region replication for disaster recovery