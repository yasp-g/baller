# CLAUDE.md - Baller Project Guidelines

## Build, Run & Test Commands
### Dependencies
- **Install dependencies**: `uv add --editable .` (project) or `uv add [package]` (single package)
- **Install dev dependencies**: `uv add --editable --dev ".[dev]"`

### Running the app
- **Production mode**: `APP_MODE=production ENV=production uv run python -m src.main`
- **Development mode**: `uv run python -m src.main`
- **Beta mode**: `APP_MODE=beta uv run python -m src.main` (enables feedback buttons)
  - **Customize feedback collection**: 
    - Enable feedback in other modes: `COLLECT_FEEDBACK=true uv run python -m src.main`
    - Customize prompt: `APP_MODE=beta FEEDBACK_PROMPT="Rate my response!" uv run python -m src.main`
    - Customize button labels: `APP_MODE=beta FEEDBACK_POSITIVE_LABEL="👍 Great!" FEEDBACK_NEGATIVE_LABEL="👎 Needs work" uv run python -m src.main`
- **Detailed logging**: `LOG_LEVEL=DEBUG uv run python -m src.main | jq -r '. | "\(.timestamp) [\(.level)] \(.logger): \(.message)"'`
- **Beta mode, detailed logging**: `APP_MODE=beta LOG_LEVEL=DEBUG uv run python -m src.main | jq -r '. | "\(.timestamp) [\(.level)] \(.logger): \(.message)"'`

### Tests
- **Run all tests**: `uv run python -m pytest tests/`
- **Run unit tests only**: `uv run python -m pytest tests/unit/`
- **Run integration tests only**: `uv run python -m pytest tests/integration/`
- **Run specific test categories**: 
  - `uv run python -m pytest tests/unit/api/` (API unit tests)
  - `uv run python -m pytest tests/unit/bot/` (Bot unit tests)
- **Run a specific test file**: `uv run python -m pytest tests/unit/api/test_llm.py`


## System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Discord Bot Interface                         │
│                               BallerBot                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              BallerCommands                            │
│                                                                        │
│  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────────┐  │
│  │  Discord Slash  │  │   Conversational  │  │  User Preferences    │  │
│  │    Commands     │  │     Interface     │  │      Management      │  │
│  └─────────────────┘  └─────────┬─────────┘  └─────────────────────┬┘  │
└─────────────────────────────────┬──────────────────────────────────┬───┘
                                  │                                  │
                                  ▼                                  │
                     ┌───────────────────────────┐                   │
                     │    Content Filtering      │                   │
                     │                           │                   │
                     │  ┌─────────────────────┐  │                   │
                     │  │  Relevance Check    │  │                   │
                     │  └─────────────────────┘  │                   │
                     │  ┌─────────────────────┐  │                   │
                     │  │    NSFW Filter      │  │                   │
                     │  └─────────────────────┘  │                   │
                     └────────────┬──────────────┘                   │
                                  │                                  │
               ┌──────────────────┴─────────────┐                    │
               ▼                                ▼                    ▼
┌────────────────────────┐      ┌─────────────────────────┐ ┌─────────────────────┐
│    Intent Processing   │      │       LLM Client        │ │  Preferences Store  │
│                        │─────▶│                         │ │                     │
│ ┌────────────────────┐ │      │ ┌─────────────────────┐ │ │  ┌───────────────┐  │
│ │  Entity Extraction │ │      │ │  Prompt Templates   │ │ │  │ User Settings │  │
│ └────────────────────┘ │      │ └─────────────────────┘ │ │  └───────────────┘  │
│ ┌────────────────────┐ │      │ ┌─────────────────────┐ │ │  ┌───────────────┐  │
│ │ Context Management │ │      │ │ Response Generation │ │ │  │Followed Teams │  │
│ └────────────────────┘ │      │ └─────────────────────┘ │ │  └───────────────┘  │
│ ┌────────────────────┐ │      │ ┌─────────────────────┐ │ │  ┌───────────────┐  │
│ │   Entity Cache     │ │      │ │   Error Tracking    │ │ │  │  AWS Storage  │  │
│ └────────────────────┘ │      │ └─────────────────────┘ │ │  └───────────────┘  │
└──────────────┬─────────┘      └──────────────┬──────────┘ └─────────────────────┘
               │                               │
               │                               │
               ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            External API Client                          │
│                                                                         │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐    │
│  │  FootballAPI    │     │   LLM APIs      │     │   Cache Layer   │    │
│  │  (football-data)│     │(Deepseek/Claude)│     │  (Local/AWS)    │    │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Components and Data Flow

| Component | Function | Key Classes | Responsibilities |
|-----------|----------|-------------|------------------|
| **Discord Interface** | User interaction | `BallerBot` | Bot initialization, event handling, command registration |
| **Command Layer** | Process commands | `BallerCommands` | Command registration, message routing, user interaction |
| **Conversation Management** | Maintain chat context | `ConversationManager` | Track message history, manage timeouts, archive conversations |
| **User Preferences** | Store user settings | `UserPreferencesManager` | Follow/unfollow teams, notification settings, persist preferences |
| **Intent System** | Understand user queries | `IntentProcessor`, `EntityExtractor` | Extract entities, detect intents, maintain conversation context |
| **Content Filtering** | Filter relevance | `ContentFilter` | Determine message relevance to football, filter inappropriate content |
| **LLM Client** | Generate responses | `LLMClient` | Format prompts, call LLM APIs, process responses |
| **Prompt Templates** | Structure prompts | `PromptTemplate` | Standardize prompts across providers, implement best practices |
| **Response Evaluation** | Quality metrics | `MetricsTracker`, `EvaluationSampler` | Track response metrics, sample responses for LLM self-evaluation |
| **Football API** | Fetch football data | `FootballAPI` | Interface with football-data.org API, handle rate limits |
| **Cache Layer** | Optimize performance | `EntityCache` | Cache API responses, sports entities, reduce API calls |

## Data Flow

1. User sends message to Discord bot
2. `BallerCommands` processes message
3. `ContentFilter` determines if message is football-relevant
4. If relevant, `IntentProcessor` determines user intent & extracts entities
5. `FootballAPI` fetches relevant football data based on intent
6. `PromptTemplate` structures a prompt with all available context
7. `LLMClient` generates response using the formatted prompt with:
   - The user message
   - Detected intent
   - Fetched football data 
   - User preferences
8. Response sent back to user via Discord
9. `EvaluationSampler` may evaluate response quality using LLM-based criteria
10. Quality metrics are tracked and available through the `!metrics` command

## Storage Systems

| System | Description | Location | Persistence |
|--------|-------------|----------|-------------|
| **Conversation History** | User message history | Memory + DynamoDB | TTL-based expiry |
| **User Preferences** | Teams followed, notification settings | Memory + DynamoDB | Persistent |
| **Entity Cache** | Teams, competitions, players | Local file cache | TTL-based refresh |

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

## Monitoring & Debugging

### Built-in Monitoring
- **Discord Commands**:
  - `!monitor`: Displays active conversations, intent stats, uptime
  - `!conversation_stats`: Shows detailed conversation metrics
  - `!metrics`: Shows LLM response quality metrics (latency, relevance, self-evaluation scores)

### Log Format
Logs are formatted as JSON for better machine processing and include:
- `timestamp`: When the event occurred
- `level`: Log level (INFO, ERROR, etc.)
- `logger`: Component that generated the log
- `message`: Human-readable description
- `component`: Subsystem (api, bot, intent, etc.)
- `request_id`: Unique ID for tracking request across components
- `user_id`: Discord user ID (when available)
- `intent`: Intent information (when processing messages)
- `duration_ms`: Performance metric for API calls

### Deployment Options

#### Local Development
```bash
# Run with debug logs
LOG_LEVEL=DEBUG uv run python -m src.main

# Follow logs with color formatting
LOG_LEVEL=DEBUG uv run python -m src.main | jq -r '. | "\(.timestamp) [\(.level)] \(.logger): \(.message)"'
```

#### Docker Deployment
```dockerfile
# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-alpine

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the application
CMD ["uv", "run", "src.main"]
```

```bash
# Build and run Docker container
docker build -t baller-bot .
docker run -e DISCORD_TOKEN=xxx -e FOOTBALL_DATA_API_KEY=xxx -e DEEPSEEK_API_KEY=xxx baller-bot
```

## AWS Integration
- **Configuration**: Enable AWS integration with `AWS_ENABLED=true` environment variable
- **DynamoDB Integration**: 
  - Conversations are stored using user_id as the partition key
  - Automatic expiry using DynamoDB TTL feature (set with `CONVERSATION_RETENTION_DAYS`)
  - Serialized data includes conversation history, metadata, and timestamps
  - User preferences stored in the same table with different prefix (PREF_)
  - Common data model with TTL and last_updated timestamps
  
### CloudWatch Integration
- JSON-formatted logs are compatible with CloudWatch Logs Insights
- Sample queries:
  ```
  # Find errors
  fields @timestamp, @message
  | filter level = "ERROR"
  | sort @timestamp desc
  | limit 20
  
  # API performance metrics
  fields @timestamp, duration_ms, resource_type
  | filter component = "sports" and duration_ms > 0
  | stats avg(duration_ms), max(duration_ms) by resource_type
  
  # User activity
  fields @timestamp, user_id, component
  | stats count(*) as activity by user_id
  | sort activity desc
  ```

- **Integration Points**:
  - `src/bot/conversation.py`: Contains AWS integration hooks for conversation storage
    - `_archive_conversation()`: Archives conversations to DynamoDB (currently placeholder)
    - `_try_load_from_aws()`: Loads previous conversations from DynamoDB (currently placeholder)
  - `src/bot/preferences.py`: Contains AWS integration hooks for user preferences
    - `_archive_preferences()`: Archives preferences to DynamoDB (currently placeholder)
    - `_try_load_from_aws()`: Loads preferences from DynamoDB (currently placeholder)

- **DynamoDB Schema Design**:
  - Partition key: `user_id` (with prefix for data type: CONV_ or PREF_)
  - Sort key: Not used in current schema (reserved for future extensions)
  - Data stored as serialized JSON in a `data` attribute
  - TTL attribute for automatic cleanup
  - `last_updated` timestamp for synchronization
  
- **Future Work**:
  - Implement actual AWS SDK calls (boto3) in the placeholder methods
  - Add AWS credentials configuration in config.py
  - Set up CloudWatch metrics for conversation statistics and user engagement
  - Implement S3 storage for large conversation contexts
  - Add GSI for team-based lookups (to find all users following a specific team)
  - Create AWS CDK/CloudFormation template for easy resource provisioning