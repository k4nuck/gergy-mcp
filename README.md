# Gergy AI - MCP Architecture Foundation

Gergy AI is an intelligent assistant powered by Model Context Protocol (MCP) architecture, designed to provide cross-domain intelligence across five key life areas: Financial, Family, Lifestyle, Professional, and Home management.

## 🏗️ Architecture Overview

This foundational implementation provides the shared infrastructure that all five MCP servers will build upon:

### Shared Infrastructure
- **Database Layer**: PostgreSQL with JSONB for flexible schema and cross-domain knowledge storage
- **Caching Layer**: Redis for high-performance caching with cross-domain relevance
- **Pattern Recognition**: Intelligent cross-domain pattern detection and suggestions
- **Cost Management**: Distributed API budget tracking and optimization
- **Base MCP Framework**: Foundation class for all domain servers

### Domain Servers
1. **Financial Server** - Budget management, expense tracking, investment insights
2. **Family Server** - Event planning, relationship management, family coordination
3. **Lifestyle Server** - Health, fitness, personal development, leisure activities
4. **Professional Server** - Career development, skill tracking, professional networking
5. **Home Server** - Home maintenance, improvement projects, household management

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested with 3.10.12)
- Docker and Docker Compose
- PostgreSQL client tools (optional for manual access)
- Redis client tools (optional for manual access)

Note: PostgreSQL and Redis will run in Docker containers, so you don't need them installed locally.

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url> gergy-mcp
cd gergy-mcp
```

2. **Environment configuration**:
```bash
cp .env.example .env
# Edit .env with your specific configuration
```

3. **Start the infrastructure**:
```bash
docker-compose up -d postgres redis
```

4. **Install dependencies**:
```bash
pip install -r requirements.txt
```

5. **Initialize database**:
```bash
python -c "
from shared.models.database import DatabaseConfig
config = DatabaseConfig('postgresql://gergy_user:gergy_password@localhost:5432/gergy_knowledge')
config.create_tables()
print('Database initialized successfully')
"
```

## 📁 Project Structure

```
gergy-mcp/
├── shared/                          # Shared infrastructure
│   ├── models/                      # Database models
│   │   ├── __init__.py
│   │   └── database.py             # PostgreSQL models with JSONB
│   ├── services/                    # Core services
│   │   ├── __init__.py
│   │   ├── database_service.py     # Unified knowledge access
│   │   ├── pattern_recognition_service.py  # Cross-domain intelligence
│   │   ├── cost_tracking_service.py        # API budget management
│   │   └── cache_service.py        # Redis caching with relevance
│   ├── utils/                       # Utilities
│   │   ├── __init__.py
│   │   └── config.py               # Configuration management
│   ├── __init__.py
│   └── base_mcp_server.py          # Base server framework
├── servers/                         # Domain-specific servers
│   ├── financial/                   # Financial management server
│   ├── family/                      # Family coordination server
│   ├── lifestyle/                   # Lifestyle management server
│   ├── professional/                # Professional development server
│   └── home/                        # Home management server
├── docker-compose.yml               # Infrastructure orchestration
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment configuration template
└── README.md                        # This file
```

## 🛠️ Key Features

### Cross-Domain Intelligence
- **Pattern Recognition**: Automatically detects patterns across domains (e.g., financial decisions affecting family plans)
- **Knowledge Sharing**: Unified knowledge base accessible across all servers
- **Context Awareness**: Maintains conversation context and suggests relevant cross-domain insights

### Performance & Cost Optimization
- **Smart Caching**: Redis-based caching with cross-domain relevance scoring
- **Cost Tracking**: Real-time API usage monitoring with budget alerts
- **Pattern-Based Suggestions**: Reduces API calls through intelligent pattern matching

### Scalable Architecture
- **Modular Design**: Each domain server inherits from `BaseMCPServer`
- **Database Flexibility**: JSONB fields allow schema evolution without migrations
- **Containerized Deployment**: Docker Compose for easy scaling and deployment

## 📊 Database Schema

### Core Tables
- **knowledge_items**: Cross-domain knowledge with flexible JSONB metadata
- **user_sessions**: Conversation tracking and context accumulation
- **temporal_cache**: Expiration management and cross-module relevance
- **cross_domain_patterns**: Pattern recognition system
- **api_usage_analytics**: Cost tracking per server

### Example Usage

```python
from shared.services.database_service import DatabaseService
from shared.services.pattern_recognition_service import PatternRecognitionService

# Initialize services
db_service = DatabaseService("postgresql://...")
pattern_service = PatternRecognitionService(db_service)

# Store knowledge across domains
await db_service.store_knowledge(
    domain="financial",
    title="Budget Planning",
    content="Monthly budget analysis...",
    metadata={"category": "planning", "priority": "high"},
    keywords=["budget", "planning", "monthly"]
)

# Detect cross-domain patterns
patterns = await pattern_service.analyze_conversation(
    content="Planning a family vacation",
    domain="family",
    session_id="user_123"
)
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://gergy_user:gergy_password@localhost:5432/gergy_knowledge

# Redis
REDIS_URL=redis://localhost:6379

# Budget limits per server (USD/day)
FINANCIAL_BUDGET_LIMIT=15.0
FAMILY_BUDGET_LIMIT=10.0
LIFESTYLE_BUDGET_LIMIT=8.0
PROFESSIONAL_BUDGET_LIMIT=12.0
HOME_BUDGET_LIMIT=8.0
```

### Server Configuration
Each domain server can be configured independently:

```python
from shared.utils.config import load_config

config = load_config("config.yml")  # Optional config file
financial_config = config.servers["financial"]
```

## 🔍 Monitoring & Analytics

### Built-in Metrics
- Request/response tracking per server
- Cost analysis and budget alerts
- Pattern detection effectiveness
- Cache hit/miss ratios
- Cross-domain suggestion accuracy

### Optional Monitoring Stack
- **Grafana**: Dashboards for visual monitoring
- **Prometheus**: Metrics collection and alerting
- **Database Analytics**: Cross-domain usage patterns

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=shared

# Run specific test modules
pytest tests/test_database_service.py
pytest tests/test_pattern_recognition.py
```

## 📈 Next Steps

This foundation enables:

1. **Domain Server Implementation**: Each server will inherit from `BaseMCPServer`
2. **Tool Registration**: Domain-specific tools for Claude.ai integration
3. **Pattern Learning**: Machine learning models for better pattern recognition
4. **API Integration**: External service connections with cost tracking
5. **Advanced Analytics**: Cross-domain insights and optimization

## 🤝 Contributing

1. Follow the established patterns in `BaseMCPServer`
2. Ensure all new features include tests
3. Update documentation for new configurations
4. Maintain cross-domain compatibility

## 📝 License

[Your chosen license]

---

**Status**: Foundation Complete ✅
**Next Phase**: Domain Server Implementation
**Target**: Full MCP integration with Claude.ai