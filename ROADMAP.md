# ROADMAP

## Progress Summary
- **Last Updated**: March 26, 2025
- **Core Infrastructure**: 92% complete (Configuration system, logging, testing, error handling, memory management)
- **NLP Enhancements**: 95% complete (Conversation management, intent detection, prompt templates, content filtering, response evaluation, streaming responses)
- **Football Data Features**: 0% complete
- **User Experience**: 40% complete (User preferences, team following, feedback collection)
- **Scalability**: 10% complete (AWS integration foundation)

## Next Steps
1. ✅ Fix failing tests to ensure full test coverage 
2. ✅ Complete error handling (custom exceptions, retry mechanisms)
3. ✅ Add conversation timeout/expiry for memory management
4. ✅ Add user preferences and team following
5. ✅ Implement intent detection system for better query understanding
6. ✅ Implement content filtering for improved relevance and safety
7. ✅ Standardize prompt templates across different LLM providers
8. Deployment and Operations (5.2), Implement AWS SDK integration (see below)
9. Reevaluate pyproject.toml and esnure it aligns with `uv` best practices
    - I'm not sure `[project.optional-dependencies]` is the best when `uv` has a built-in development dependencies workflow (`[dependency-groups]`)
10. Implement caching for frequently accessed football data


## 1. Core Infrastructure Improvements

### 1.1 Error Handling
- ✅ Implement custom exception classes for different error types
- ✅ Add proper error logging and monitoring
- ✅ Improve user-facing error messages with helpful guidance
- ✅ Add retry mechanisms for transient API failures

### 1.2 Configuration Management
- ✅ Move hardcoded values to configuration (e.g., API endpoints, model names)
- ✅ Add configuration validation at startup
- ✅ Support different environment configurations (dev, test, prod)

### 1.3 Testing Infrastructure
- ✅ Implement unit tests with pytest for all components
- ✅ Add mocks for external services (Discord, Football API, LLM)
- ✅ Set up CI pipeline for automated testing
- ✅ Add test coverage reporting

## 2. Natural Language Processing Enhancements

### 2.1 Intent Detection
- ✅ Replace keyword matching with structured intent recognition
  - Implemented resource-aware intent system that maps intents to API endpoints
  - Created entity extraction system for competitions, teams, timeframes, etc.
  - Added graceful fallback to keyword matching for backward compatibility
- ✅ Implement entity extraction (teams, players, competitions)
  - Created pattern-based entity extraction for competitions and timeframes
  - Added team entity recognition with ID resolution
  - Implemented entity caching system for improved performance
- ✅ Add context awareness for multi-turn conversations
  - Implemented conversation context tracking across multiple turns
  - Added entity and intent history with confidence decay over time
  - Support for follow-up questions that reference previous entities
- ✅ Support for common football-related queries and commands
  - Added support for standings, matches, teams, and scorers queries
  - Implemented context-sensitive intent resolution

### 2.2 Conversation Management
- ✅ Improve conversation history management with proper state tracking
- ✅ Add timeout/expiry for old conversations to manage memory
- Implement conversation context summarization for long interactions
- ✅ Support user preferences and personalization
- ✅ Implement content filtering for football relevance and NSFW detection

### 2.3 LLM Integration
- ✅ Standardize prompt templates across different providers
  - Implemented modular prompt template system with provider detection
  - Created template registry for easy template management
  - Added support for multiple LLM providers (Deepseek, Anthropic)
  - Implemented consistent formatting and structure across templates
- ✅ Implement prompt engineering best practices
  - Added clear role definitions and explicit instructions
  - Implemented structured formatting with section markers
  - Created specialized templates for different use cases
  - Added provider-specific rendering for optimal performance
- ✅ Add evaluation metrics for response quality
  - Implemented metrics tracking system for latency, relevance, and error rates
  - Created LLM-based self-evaluation system with detailed quality criteria
  - Added probabilistic sampling to evaluate a percentage of responses
  - Implemented user feedback collection via Discord UI buttons
  - Integrated feedback with metrics visualization in the Discord interface
  - Added comprehensive test coverage for evaluation components
- ✅ Support streaming responses for faster user experience
  - Implemented streaming for both Anthropic and OpenAI/Deepseek providers
  - Added real-time message updates as responses are generated
  - Created buffer system to manage Discord message updates efficiently
  - Optimized user experience with immediate partial responses

## 3. Football Data Features

### 3.1 Enhanced Data Integration
- Support more football data endpoints and query types
- Add caching layer for frequently accessed data
- Implement data validation and normalization
- Support multiple seasons and historical data

### 3.2 Data Visualization
- Add charts and graphs for standings and statistics
- Support interactive embeds in Discord messages
- Implement exportable reports for match summaries
- Add team and player comparison features

## 4. User Experience Improvements

### 4.1 Command System
- Implement rich Discord slash commands
- Add autocomplete for team and competition names
- Support natural language commands through message interactions
- Implement help system with examples and guided flows

### 4.2 Personalization
- ✅ Allow users to set favorite teams and competitions
  - Implemented team following via `!follow` and `!unfollow` commands
  - Added team preferences storage with AWS integration architecture
  - Enhanced `!matches` command to support filtering by followed teams
  - Added notification preference settings for future game reminders
- ✅ Add feedback collection system
  - Implemented button-based feedback interface in Discord UI
  - Created configurable environment modes (development, beta, production)
  - Added metrics tracking for user feedback scores
  - Feedback metrics integrated with existing evaluation system
- Implement notification system for match events
- Support customization of data presentation
- Add user-specific command shortcuts

## 5. Scalability and Performance

### 5.1 API Optimization
- Implement proper rate limiting for external APIs
- Add request batching for related data
- Optimize response payload sizes
- Implement query parameter validation

### 5.2 Deployment and Operations
- Containerize application with Docker
- Set up monitoring and alerting
- ✅ Implement database for persistent storage (AWS DynamoDB foundation)
  - Added conversation persistence architecture with DynamoDB integration hooks
  - Implemented TTL-based expiry mechanism using DynamoDB's TTL feature
  - Added configuration toggles for AWS integration (AWS_ENABLED env var)
  - Prepared serialization/deserialization for AWS storage
  - Extended AWS integration for user preferences storage
  - Designed unified DynamoDB schema with prefixes for different data types
  - Added architecture for scaling user preferences with DynamoDB
    - Partition key design using user_id with prefixes for data type separation
    - Global secondary indexes for team-based lookups (future implementation)
    - Optimized for high-read, low-write access patterns
    - Planned support for eventual consistency model for distributed deployment
- ✅ Create comprehensive database plan and schema design
  - Designed a complete data storage strategy for all messaging pipeline components
  - Created schema definitions for DynamoDB tables, S3 storage, and OpenSearch
  - Built data lifecycle management plans for cost optimization
  - Defined proper relationships between storage components
- ✅ Implement infrastructure as code with OpenTofu
  - Created modular OpenTofu configuration for all AWS resources
  - Built environment-specific configurations (dev, staging, prod)
  - Implemented hierarchical variable management system
  - Set up remote state storage with Scalr backend
  - Created example configuration files for easy setup
  - ✅ Implemented detailed resource definitions:
    - DynamoDB tables with optimized key design and GSIs
    - S3 buckets with security configuration and lifecycle rules
    - OpenSearch domain with performance and scaling settings
    - Comprehensive resource outputs and IAM policy support
- Implement AWS SDK integration
  - Implement boto3 integration in conversation.py for DynamoDB storage
  - Implement boto3 integration in preferences.py for DynamoDB storage
  - Add AWS credentials configuration in config.py
  - Set up CloudWatch metrics for conversation statistics and user engagement
  - Create deployment pipeline for infrastructure
- Prepare for multi-instance deployment