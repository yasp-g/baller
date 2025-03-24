# CLAUDE.md - Baller Project Guidelines

## Build & Test Commands
- **Run tests**: `uv run python -m pytest tests/` or `uv run python -m tests.test_api` or `uv run python -m tests.test_commands` or `uv run python -m tests.test_llm`
- **Install dependencies**: `uv add --editable .` (project) or `uv add [package]` (single package)
- **Install dev dependencies**: `uv add --editable --dev ".[dev]"`
- **Run the app**: `uv run python -m src.main`

## Code Style Guidelines
- **Imports**: Standard lib first, third-party second, relative imports last
- **Type hints**: Use for function parameters and return types
- **Naming**: CamelCase for classes, snake_case for functions/variables, UPPERCASE for constants
- **Error handling**: Use try/except blocks with specific exceptions, avoid bare excepts
- **Docstrings**: Triple double-quotes with clear purpose description
- **Async pattern**: Use async/await consistently with proper client closure
- **HTTP client**: Use httpx's AsyncClient and raise_for_status() for errors
- **Classes**: Modular design with clear separation of API vs Bot concerns

## Structure
- `/src/api/`: External API integrations
- `/src/bot/`: Discord bot functionality 
- `/tests/`: Integration tests for each module

## Commit Guidelines
- **Atomic commits**: Each commit should represent a single logical change
- **Commit message format**:
  ```
  <type>(<scope>): <short summary>
  
  <optional body>
  ```
- **Types**: feat, fix, docs, style, refactor, test, chore
- **Scopes**: api, bot, config, llm, test, deps, infra
- **Examples**:
  - `feat(api): Add team player stats endpoint`
  - `fix(bot): Handle missing data in conversation response`
  - `refactor(llm): Standardize prompt templates`
- **First line**: Maximum 72 characters, no period at end
- **Body**: Optional, used for explaining complex changes or breaking changes
- **Pull requests**: Should reference related issues with "Fixes #123" or "Addresses #123"

## General Notes
- **Deployment Infrastructure**: AWS services will be used to deploy and support the application
  - Terraform will be used for managing infrastructure as code

## AWS Integration
- **Configuration**: Enable AWS integration with `AWS_ENABLED=true` environment variable
- **DynamoDB Integration**: 
  - Conversations are stored using user_id as the partition key
  - Automatic expiry using DynamoDB TTL feature (set with `CONVERSATION_RETENTION_DAYS`)
  - Serialized data includes conversation history, metadata, and timestamps
- **Integration Points**:
  - `src/bot/conversation.py`: Contains AWS integration hooks for conversation storage
  - `_archive_conversation()`: Archives conversations to DynamoDB (currently placeholder)
  - `_try_load_from_aws()`: Loads previous conversations from DynamoDB (currently placeholder)
- **Future Work**:
  - Implement actual AWS SDK calls (boto3) in the placeholder methods
  - Add AWS credentials configuration in config.py
  - Set up CloudWatch metrics for conversation statistics
  - Implement S3 storage for large conversation contexts