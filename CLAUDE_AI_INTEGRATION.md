# Claude.ai Pro MCP Server Integration Guide

## Quick Setup Instructions

### 1. Financial Server (WORKING)
- **URL**: `https://ha-main-remote.tail9144d.ts.net/mcp/sse`
- **Name**: Gergy Financial Assistant
- **Description**: Personal financial data management with 8 tools for transactions, balances, and insights

### 2. Family Server (TO BE IMPLEMENTED)
- **URL**: `https://ha-main-remote.tail9144d.ts.net/family/mcp/sse`
- **Name**: Gergy Family Coordinator
- **Description**: Family calendar, activities, and coordination management

### 3. Home Server (TO BE IMPLEMENTED)
- **URL**: `https://ha-main-remote.tail9144d.ts.net/home/mcp/sse`
- **Name**: Gergy Home Manager
- **Description**: Home maintenance, inventory, and household task coordination

### 4. Lifestyle Server (TO BE IMPLEMENTED)
- **URL**: `https://ha-main-remote.tail9144d.ts.net/lifestyle/mcp/sse`
- **Name**: Gergy Lifestyle Coach
- **Description**: Personal goals, fitness, nutrition, and wellness tracking

### 5. Professional Server (TO BE IMPLEMENTED)
- **URL**: `https://ha-main-remote.tail9144d.ts.net/professional/mcp/sse`
- **Name**: Gergy Career Assistant
- **Description**: Professional development, networking, and project management

## Claude.ai Pro Configuration

### Adding MCP Servers in Claude.ai Pro

1. **Access MCP Settings**:
   - Open Claude.ai Pro
   - Navigate to Settings > Integrations > Model Context Protocol

2. **Add New Server**:
   - Click "Add Server"
   - Enter the connection details for each server:

#### Connection Settings Template
```
Name: [Server Name from above]
URL: [Server URL from above]  
Protocol: MCP over SSE
Authentication: None
Description: [Description from above]
```

#### Advanced Settings (if available)
```
Transport: Server-Sent Events (SSE)
Protocol Version: 2025-06-18
Headers: None required
Timeout: 30 seconds
```

### Available Tools by Server

#### Financial Server Tools (8 tools)
1. **retrieve_financial_context** - Get relevant financial data with filters
2. **store_financial_data** - Store transactions, balances, goals, etc.
3. **get_financial_summary** - Current financial snapshot
4. **search_financial_history** - Search historical financial data
5. **get_pattern_insights** - Cross-domain financial patterns
6. **search_knowledge** - Search financial knowledge base
7. **get_usage_stats** - API usage and cost tracking
8. **store_knowledge** - Store financial insights and notes

#### Family Server Tools (6 tools - when implemented)
1. **manage_family_calendar** - Schedule and coordinate family events
2. **track_family_activities** - Log and organize family activities
3. **plan_family_events** - Event planning with budget integration
4. **manage_family_contacts** - Contact and relationship management
5. **coordinate_family_tasks** - Task assignment and tracking
6. **track_family_health** - Health and wellness coordination

#### Home Server Tools (6 tools - when implemented)
1. **manage_home_maintenance** - Maintenance scheduling and tracking
2. **track_home_inventory** - Household item and warranty management
3. **plan_home_improvements** - Renovation and improvement planning
4. **manage_utilities_services** - Utility and service provider management
5. **track_home_security** - Security system and monitoring
6. **coordinate_household_tasks** - Cleaning and organization scheduling

#### Lifestyle Server Tools (6 tools - when implemented)
1. **manage_personal_goals** - Personal development and goal tracking
2. **track_fitness_activities** - Exercise and wellness logging
3. **plan_meals_nutrition** - Meal planning and nutrition tracking
4. **manage_hobbies_interests** - Hobby and interest organization
5. **track_entertainment** - Entertainment preferences and history
6. **manage_personal_schedule** - Personal time management

#### Professional Server Tools (6 tools - when implemented)
1. **manage_career_goals** - Career development planning
2. **track_professional_network** - Contact and networking management
3. **manage_projects_tasks** - Work project coordination
4. **track_skills_development** - Skill building and certification tracking
5. **manage_work_schedule** - Professional calendar management
6. **analyze_career_progress** - Career advancement insights

## Usage Examples

### Financial Server Usage
```
"Help me analyze my spending for the last 3 months"
"Store this transaction: $45 for groceries at Whole Foods"
"What's my current financial summary?"
"Search for all dining expenses over $50"
```

### Family Server Usage (when ready)
```
"Schedule a family vacation for next month"
"Track our daughter's soccer practice schedule"
"Plan a birthday party with a $300 budget"
"Coordinate household chores for this week"
```

### Cross-Domain Intelligence
The Gergy system automatically detects patterns across domains:
- Financial planning events that affect family activities
- Home improvement projects that impact budgets
- Family events that require financial coordination
- Career changes affecting lifestyle and financial goals

## Troubleshooting

### Common Issues

1. **"Trouble connecting to server"**
   - Verify URL is exactly as listed above
   - Ensure HTTPS is being used
   - Check that authentication is set to "None"

2. **"Authentication failed"**
   - Confirm authentication is set to "None" 
   - Do not use OAuth or API keys
   - MCP servers are configured for no-auth access

3. **"Protocol version mismatch"**
   - This should not occur with current implementation
   - Servers use MCP protocol version 2025-06-18

### Network Requirements
- Servers are accessible via Tailscale Funnel (no VPN required)
- Uses trusted SSL certificates from No-IP
- Standard HTTPS port access (8000-8004)
- No firewall configuration needed

### Support
If issues persist:
1. Check server logs: `docker-compose logs [server-name]-server`
2. Verify server is running: `docker-compose ps`
3. Test direct HTTPS access to verify SSL certificate

## Security & Privacy

### Data Storage
- All data stored locally in PostgreSQL database
- No data transmitted to external services
- Cross-domain patterns stored for intelligent suggestions
- Personal financial and family data remains private

### Access Control
- Servers only accessible via Tailscale Funnel
- No public internet exposure
- SSL encryption for all communications
- No authentication logs or tracking

### Data Retention
- Knowledge items stored indefinitely for pattern recognition
- Conversation context maintained across sessions
- API usage tracked for cost monitoring only
- No personal data sharing between domains without explicit requests

## Getting Started

1. **Start with Financial Server** - Already working and configured
2. **Test basic functionality** - Store a transaction, get summary
3. **Explore cross-domain features** - Use pattern insights
4. **Add remaining servers** - As they become available
5. **Leverage full ecosystem** - Use multiple servers for comprehensive assistance

The system is designed to provide increasingly intelligent suggestions as you use multiple servers and build up your personal knowledge base across all life domains.