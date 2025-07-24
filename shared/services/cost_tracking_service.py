"""
CostTrackingService for distributed API budget management across MCP servers.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)

class APIProvider(Enum):
    """Supported API providers for cost tracking."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    CUSTOM = "custom"

@dataclass
class CostRates:
    """Cost rates per token for different API providers."""
    input_cost_per_1k: float
    output_cost_per_1k: float
    provider: APIProvider
    model: str

@dataclass
class APIUsage:
    """Represents a single API usage event."""
    server_name: str
    provider: APIProvider
    model: str
    endpoint: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    timestamp: datetime
    metadata: Dict[str, Any]

class CostTrackingService:
    """Service for tracking and managing API costs across all MCP servers."""
    
    def __init__(self, database_service, daily_budget_limit: float = 50.0):
        self.db = database_service
        self.daily_budget_limit = daily_budget_limit
        self.cost_rates = self._initialize_cost_rates()
        self.usage_cache = {}
        self.alerts_sent = set()
        
    def _initialize_cost_rates(self) -> Dict[str, CostRates]:
        """Initialize cost rates for different API providers and models."""
        return {
            # OpenAI GPT models
            'openai_gpt-4': CostRates(0.03, 0.06, APIProvider.OPENAI, 'gpt-4'),
            'openai_gpt-4-turbo': CostRates(0.01, 0.03, APIProvider.OPENAI, 'gpt-4-turbo'),
            'openai_gpt-3.5-turbo': CostRates(0.001, 0.002, APIProvider.OPENAI, 'gpt-3.5-turbo'),
            
            # Anthropic Claude models
            'anthropic_claude-3-opus': CostRates(0.015, 0.075, APIProvider.ANTHROPIC, 'claude-3-opus'),
            'anthropic_claude-3-sonnet': CostRates(0.003, 0.015, APIProvider.ANTHROPIC, 'claude-3-sonnet'),
            'anthropic_claude-3-haiku': CostRates(0.00025, 0.00125, APIProvider.ANTHROPIC, 'claude-3-haiku'),
            
            # Google models
            'google_gemini-pro': CostRates(0.001, 0.002, APIProvider.GOOGLE, 'gemini-pro'),
            'google_gemini-ultra': CostRates(0.01, 0.03, APIProvider.GOOGLE, 'gemini-ultra'),
            
            # Azure OpenAI
            'azure_gpt-4': CostRates(0.03, 0.06, APIProvider.AZURE, 'gpt-4'),
            'azure_gpt-35-turbo': CostRates(0.001, 0.002, APIProvider.AZURE, 'gpt-35-turbo'),
        }
    
    async def track_api_usage(
        self,
        server_name: str,
        provider: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Dict[str, Any] = None
    ) -> APIUsage:
        """Track a single API usage event."""
        provider_enum = APIProvider(provider.lower())
        rate_key = f"{provider.lower()}_{model}"
        
        # Get cost rates
        if rate_key in self.cost_rates:
            rates = self.cost_rates[rate_key]
        else:
            # Default rates for unknown models
            rates = CostRates(0.001, 0.002, provider_enum, model)
            logger.warning(f"Unknown model {rate_key}, using default rates")
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * rates.input_cost_per_1k
        output_cost = (output_tokens / 1000) * rates.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        # Create usage record
        usage = APIUsage(
            server_name=server_name,
            provider=provider_enum,
            model=model,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=total_cost,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store in database
        await self._store_usage(usage)
        
        # Check budget limits
        await self._check_budget_limits(server_name, total_cost)
        
        return usage
    
    async def _store_usage(self, usage: APIUsage):
        """Store usage data in database."""
        with self.db.get_session() as session:
            from ..models.database import APIUsageAnalytics
            
            analytics = APIUsageAnalytics(
                server_name=usage.server_name,
                api_provider=usage.provider.value,
                endpoint=usage.endpoint,
                request_count=1,
                token_usage={
                    'input': usage.input_tokens,
                    'output': usage.output_tokens,
                    'model': usage.model
                },
                estimated_cost=usage.estimated_cost,
                date=usage.timestamp,
                metadata=usage.metadata
            )
            session.add(analytics)
    
    async def _check_budget_limits(self, server_name: str, cost: float):
        """Check if usage exceeds budget limits and send alerts."""
        daily_usage = await self.get_daily_usage(server_name)
        
        # Check various thresholds
        thresholds = [
            (0.5, "50% of daily budget used"),
            (0.8, "80% of daily budget used"),
            (0.9, "90% of daily budget used"),
            (1.0, "Daily budget limit exceeded!")
        ]
        
        for threshold, message in thresholds:
            if (daily_usage['total_cost'] >= self.daily_budget_limit * threshold and 
                f"{server_name}_{threshold}" not in self.alerts_sent):
                
                await self._send_budget_alert(server_name, message, daily_usage)
                self.alerts_sent.add(f"{server_name}_{threshold}")
    
    async def _send_budget_alert(
        self, 
        server_name: str, 
        message: str, 
        usage_data: Dict[str, Any]
    ):
        """Send budget alert (implement based on notification preferences)."""
        alert_data = {
            'server_name': server_name,
            'message': message,
            'current_cost': usage_data['total_cost'],
            'daily_limit': self.daily_budget_limit,
            'timestamp': datetime.utcnow().isoformat(),
            'usage_breakdown': usage_data
        }
        
        logger.warning(f"BUDGET ALERT: {message} for {server_name}")
        logger.info(f"Usage details: {json.dumps(alert_data, indent=2)}")
        
        # Store alert in database for tracking
        await self.db.store_knowledge(
            domain="system",
            title=f"Budget Alert: {server_name}",
            content=json.dumps(alert_data, indent=2),
            metadata={'type': 'budget_alert', 'severity': 'warning'},
            keywords=['budget', 'alert', 'cost', server_name]
        )
    
    async def get_daily_usage(self, server_name: str = None) -> Dict[str, Any]:
        """Get usage for current day."""
        return await self.db.get_api_usage_summary(server_name, days=1)
    
    async def get_weekly_usage(self, server_name: str = None) -> Dict[str, Any]:
        """Get usage for current week."""
        return await self.db.get_api_usage_summary(server_name, days=7)
    
    async def get_monthly_usage(self, server_name: str = None) -> Dict[str, Any]:
        """Get usage for current month."""
        return await self.db.get_api_usage_summary(server_name, days=30)
    
    async def get_cost_optimization_suggestions(self, server_name: str) -> List[Dict[str, Any]]:
        """Get suggestions for optimizing API costs."""
        suggestions = []
        
        # Get usage patterns
        weekly_usage = await self.get_weekly_usage(server_name)
        
        if not weekly_usage['daily_breakdown']:
            return suggestions
        
        # Analyze usage patterns
        daily_costs = [day['cost'] for day in weekly_usage['daily_breakdown'].values()]
        avg_daily_cost = sum(daily_costs) / len(daily_costs)
        
        if avg_daily_cost > self.daily_budget_limit * 0.8:
            suggestions.append({
                'type': 'budget_warning',
                'priority': 'high',
                'message': f'Average daily cost (${avg_daily_cost:.2f}) approaching limit (${self.daily_budget_limit})',
                'recommendation': 'Consider using more cost-effective models or reducing API calls'
            })
        
        # Check for expensive models being used frequently
        usage_by_model = await self._analyze_model_usage(server_name)
        for model, usage in usage_by_model.items():
            if usage['cost_per_request'] > 0.10:  # More than 10 cents per request
                suggestions.append({
                    'type': 'model_optimization',
                    'priority': 'medium',
                    'message': f'Model {model} has high cost per request (${usage["cost_per_request"]:.3f})',
                    'recommendation': f'Consider using a more cost-effective model for routine tasks'
                })
        
        # Check for peak usage times
        hourly_usage = await self._analyze_hourly_usage(server_name)
        peak_hours = [hour for hour, cost in hourly_usage.items() if cost > avg_daily_cost * 0.2]
        
        if len(peak_hours) > 0:
            suggestions.append({
                'type': 'usage_pattern',
                'priority': 'low',
                'message': f'Peak usage detected during hours: {", ".join(peak_hours)}',
                'recommendation': 'Consider implementing caching or rate limiting during peak hours'
            })
        
        return suggestions
    
    async def _analyze_model_usage(self, server_name: str) -> Dict[str, Dict[str, float]]:
        """Analyze usage patterns by model."""
        # This would typically query the database for detailed model usage
        # For now, return a placeholder structure
        return {
            'gpt-4': {'requests': 50, 'total_cost': 5.0, 'cost_per_request': 0.10},
            'gpt-3.5-turbo': {'requests': 200, 'total_cost': 2.0, 'cost_per_request': 0.01}
        }
    
    async def _analyze_hourly_usage(self, server_name: str) -> Dict[str, float]:
        """Analyze usage patterns by hour of day."""
        # This would typically query the database for hourly breakdowns
        # For now, return a placeholder structure
        return {
            '09:00': 0.50, '10:00': 0.75, '11:00': 1.20, '12:00': 0.30,
            '13:00': 0.60, '14:00': 1.50, '15:00': 1.80, '16:00': 0.90
        }
    
    async def set_budget_limit(self, server_name: str, daily_limit: float):
        """Set custom budget limit for a specific server."""
        # Store in database or configuration
        await self.db.store_knowledge(
            domain="system",
            title=f"Budget Limit: {server_name}",
            content=f"Daily budget limit set to ${daily_limit}",
            metadata={'type': 'budget_config', 'server': server_name, 'limit': daily_limit},
            keywords=['budget', 'limit', 'config', server_name]
        )
        
        logger.info(f"Budget limit for {server_name} set to ${daily_limit}")
    
    async def get_cost_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive cost report."""
        report = {
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'total_summary': await self.db.get_api_usage_summary(days=days),
            'server_breakdown': {},
            'cost_trends': {},
            'optimization_opportunities': []
        }
        
        # Get breakdown by server
        servers = ['financial', 'family', 'lifestyle', 'professional', 'home']
        for server in servers:
            server_usage = await self.db.get_api_usage_summary(server, days)
            report['server_breakdown'][server] = server_usage
            
            # Get optimization suggestions for each server
            optimizations = await self.get_cost_optimization_suggestions(server)
            if optimizations:
                report['optimization_opportunities'].extend(optimizations)
        
        return report
    
    def reset_daily_alerts(self):
        """Reset daily alert tracking (call at midnight)."""
        self.alerts_sent.clear()
        logger.info("Daily alert tracking reset")