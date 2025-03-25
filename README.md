# Baller: Conversational Football Discord Bot

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python Version](https://img.shields.io/badge/python-3.13-blue)
![Status](https://img.shields.io/badge/status-under%20development-yellow)

Baller is an intelligent Discord bot that provides conversational access to football (soccer) data. Powered by large language models and integrated with football data APIs, Baller enables fans to have natural conversations about matches, standings, teams, and more.

## Features

### Natural Language Understanding
- **Conversational Interface**: Chat with Baller about football topics using natural language
- **Intent Recognition**: Automatically detects what information you're looking for
- **Entity Extraction**: Identifies teams, players, competitions, and other football entities in your messages

### Football Data & Analysis
- **Live Scores**: Get real-time match information and scores
- **Standings**: View league tables for major competitions
- **Team Information**: Access details about teams, players, and upcoming fixtures
- **Follow Teams**: Track your favorite teams and get personalized updates

### Personalization
- **Team Following**: Save your favorite teams for quick access to their information
- **Conversation Memory**: Bot remembers context from earlier in your conversation
- **Relevance Filtering**: Ensures responses stay focused on football topics

## Example Interactions

```
User: How did Chelsea do in their last match?
Baller: Chelsea drew 1-1 with Aston Villa in their Premier League match on Saturday. 
Madueke scored for Chelsea in the 62nd minute, but Bailey equalized for 
Villa in the 85th minute.

User: When do they play next?
Baller: Chelsea's next match is against Crystal Palace in the Premier League. 
The match is scheduled for Wednesday, April 2nd at 20:00 GMT at Stamford Bridge.

User: !follow Chelsea
Baller: You're now following Chelsea FC! I'll prioritize their matches and updates for you.

User: Show me the current Premier League standings
Baller: *[Displays current Premier League table with team positions, points, etc.]*
```

## Commands

Baller supports both conversational interaction and explicit commands:

### Discord Slash Commands
- `/standings [competition]` - Show league standings
- `/matches [team] [timeframe]` - Show recent and upcoming matches
- `/competitions` - List available competitions

### Text Commands
- `!follow <team>` - Add a team to your followed teams
- `!unfollow <team>` - Remove a team from your followed teams
- `!my_teams` - List your followed teams
- `!monitor` - Display bot performance metrics and status
- `!conversation_stats` - Show statistics about active conversations
- `!metrics` - View response quality metrics

## Architecture

Baller is built with a modular design that combines:

- **Discord API Integration**: For message handling and user interaction
- **Intent Processing System**: To understand the meaning behind user messages
- **LLM Integration**: Leveraging language models for natural conversation
- **Football Data API**: Accessing real-time sports data
- **AWS Backend**: For data persistence and scalability

The system uses streaming responses, intelligent caching, and context management to provide a responsive and engaging user experience.

## Contributing

Baller is under active development. More details about contributing will be made available as the project matures.

## License

This project is licensed under the MIT License - see the LICENSE file for details.