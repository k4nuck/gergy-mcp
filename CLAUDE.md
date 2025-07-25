# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Database Setup
```bash
# Start infrastructure services
docker-compose up -d postgres redis

# Initialize database tables
python -c "
from shared.models.database import DatabaseConfig
import os
config = DatabaseConfig(os.getenv('DATABASE_URL'))
config.create_tables()
print('Database initialized successfully')
"
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=shared

# Run specific test modules
pytest tests/test_database_service.py
pytest tests/test_pattern_recognition.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8

# Type checking
mypy shared/
```

### Docker Operations
```bash
# Start all services (infrastructure + MCP servers)
docker-compose up -d

# Start only infrastructure
docker-compose up -d postgres redis

# Start specific domain server
docker-compose up -d financial-server

# View logs
docker-compose logs -f financial-server
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
```

## Architecture Overview

### Core Components

**BaseMCPServer** (`shared/base_mcp_server.py`): Foundation class that all domain servers inherit from. Provides:
- MCP tool registration and handling
- Cross-domain pattern recognition
- Cost tracking and budget management
- Session management and context preservation
- Standard tools (knowledge search, pattern insights, usage stats)

**DatabaseService** (`shared/services/database_service.py`): Unified data access layer with:
- Cross-domain knowledge storage with JSONB flexibility
- Session tracking and conversation history
- Pattern storage and retrieval
- API usage analytics

**PatternRecognitionService** (`shared/services/pattern_recognition_service.py`): Intelligent cross-domain pattern detection:
- Pre-defined pattern templates (financial planning, home improvement, etc.)
- Trigger-based pattern matching
- Confidence scoring and domain coverage analysis
- Pattern-based suggestions generation

### Database Schema

**Core Tables:**
- `knowledge_items`: Cross-domain knowledge with JSONB metadata and keyword indexing
- `user_sessions`: Conversation tracking with context accumulation
- `temporal_cache`: Redis-backed caching with cross-domain relevance
- `cross_domain_patterns`: Pattern recognition system storage
- `api_usage_analytics`: Cost tracking per server with token usage

### Domain Server Structure

Each domain server (financial, family, lifestyle, professional, home) inherits from `BaseMCPServer` and implements:
- `register_domain_tools()`: Domain-specific MCP tools
- Custom tool handlers for domain functionality
- Integration with shared services (database, cache, patterns, cost tracking)

### Cross-Domain Intelligence

The system provides intelligent suggestions by:
1. **Pattern Detection**: Analyzing conversation content for trigger keywords across domains
2. **Context Sharing**: Maintaining session context that spans multiple domains
3. **Cache Relevance**: Storing cache entries with cross-domain relevance scores
4. **Knowledge Linking**: JSONB-based flexible schema allows linking related concepts

### Configuration

**Environment Variables:** All configuration through `.env` file including:
- Database and Redis URLs
- Per-server budget limits
- Debug flags and logging levels
- Optional monitoring enablement

**Budget Management:** Built-in cost tracking with configurable daily limits per domain server, token usage monitoring, and budget alerts.

### Docker Architecture

**Multi-Service Setup:**
- PostgreSQL: Persistent knowledge and analytics storage
- Redis: High-performance caching with cross-domain intelligence
- 5 Domain Servers: Each with independent scaling and resource limits
- Optional Monitoring: Grafana and Prometheus for analytics

### Pattern Templates

The system includes pre-configured pattern detection for:
- Financial planning events affecting family and lifestyle
- Home improvement projects involving financial and family coordination
- Family activity planning with budget implications
- Career development impacting financial and lifestyle goals
- Health/lifestyle changes affecting family and financial planning

### Development Workflow

1. **Shared Infrastructure First**: All domain servers depend on shared services
2. **Pattern-Driven Development**: New features should consider cross-domain implications
3. **Cost-Aware Design**: All external API calls tracked and budgeted
4. **Context Preservation**: Session state maintained across domain interactions