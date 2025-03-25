# ROADMAP

## Progress Summary
- **Last Updated**: March 25, 2025
- **Core Infrastructure**: 92% complete (Configuration system, logging, testing, error handling, memory management)
- **NLP Enhancements**: 90% complete (Conversation management, intent detection, prompt templates, content filtering, response evaluation)
- **Football Data Features**: 0% complete
- **User Experience**: 25% complete (User preferences, team following)
- **Scalability**: 10% complete (AWS integration foundation)

## Next Steps
1. ✅ Fix failing tests to ensure full test coverage 
2. ✅ Complete error handling (custom exceptions, retry mechanisms)
3. ✅ Add conversation timeout/expiry for memory management
4. ✅ Add user preferences and team following
5. ✅ Implement intent detection system for better query understanding
6. ✅ Implement content filtering for improved relevance and safety
7. ✅ Standardize prompt templates across different LLM providers
8. Implement caching for frequently accessed football data

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
  - Integrated metrics visualization with the Discord bot interface
  - Added comprehensive test coverage for evaluation components
- ✅ Support streaming responses for faster user experience

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
- Prepare for multi-instance deployment