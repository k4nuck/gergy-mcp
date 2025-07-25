"""
BaseMCPServer - Foundation class that all 5 domain servers inherit from.
Provides standard MCP integration, pattern recognition, and cost management.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
import json
import os
from dataclasses import dataclass

# MCP imports - Official MCP SDK
from mcp.server import FastMCP
from mcp import Tool
from mcp.types import TextContent, ImageContent, CallToolRequest

from .services.database_service import DatabaseService
from .services.pattern_recognition_service import PatternRecognitionService
from .services.cost_tracking_service import CostTrackingService
from .services.cache_service import CacheService

logger = logging.getLogger(__name__)

@dataclass
class MCPToolDefinition:
    """Definition for an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable

class BaseMCPServer(ABC):
    """Base class for all Gergy MCP domain servers."""
    
    def __init__(
        self,
        domain_name: str,
        database_url: str,
        redis_url: str = "redis://localhost:6379",
        daily_budget_limit: float = 10.0
    ):
        self.domain_name = domain_name
        self.server_name = f"gergy-{domain_name}"
        
        # Initialize shared services
        self.db_service = DatabaseService(database_url)
        self.pattern_service = PatternRecognitionService(self.db_service)
        self.cost_service = CostTrackingService(self.db_service, daily_budget_limit)
        self.cache_service = CacheService(self.db_service, redis_url)
        
        # MCP Server instance
        self.mcp_server = FastMCP(name=self.server_name)
        
        # Tool registry
        self.tools: Dict[str, MCPToolDefinition] = {}
        self.current_session_id: Optional[str] = None
        self.session_context: Dict[str, Any] = {}
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
    async def initialize(self):
        """Initialize all services and register tools."""
        try:
            # Initialize services
            await self.cache_service.initialize()
            
            # Register domain-specific tools
            await self.register_domain_tools()
            
            # Register standard tools available to all domains
            await self.register_standard_tools()
            
            # Set up MCP handlers
            self._setup_mcp_handlers()
            
            logger.info(f"Initialized {self.server_name} with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.server_name}: {e}")
            raise
    
    @abstractmethod
    async def register_domain_tools(self):
        """Register domain-specific tools. Must be implemented by subclasses."""
        pass
    
    async def register_standard_tools(self):
        """Register standard tools available to all domains."""
        
        # Knowledge search tool
        self.register_tool(
            name="search_knowledge",
            description="Search the knowledge base across domains",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Domains to search (optional)"
                    },
                    "limit": {"type": "integer", "default": 10, "description": "Max results"}
                },
                "required": ["query"]
            },
            handler=self._handle_knowledge_search
        )
        
        # Pattern insights tool
        self.register_tool(
            name="get_pattern_insights",
            description="Get intelligent pattern-based suggestions",
            parameters={
                "type": "object",
                "properties": {
                    "context": {"type": "string", "description": "Current context or query"}
                },
                "required": ["context"]
            },
            handler=self._handle_pattern_insights
        )
        
        # Session context tool
        self.register_tool(
            name="update_session_context",
            description="Update session context with new information",
            parameters={
                "type": "object",
                "properties": {
                    "context_update": {
                        "type": "object",
                        "description": "Context data to add or update"
                    },
                    "conversation_entry": {
                        "type": "object", 
                        "description": "Conversation entry to log"
                    }
                },
                "required": ["context_update"]
            },
            handler=self._handle_session_update
        )
        
        # Cost tracking tool
        self.register_tool(
            name="get_usage_stats",
            description="Get API usage and cost statistics",
            parameters={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly"],
                        "default": "daily"
                    }
                }
            },
            handler=self._handle_usage_stats
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """Register a tool with the MCP server."""
        tool_def = MCPToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )
        self.tools[name] = tool_def
        
        # Wrap handler with standard functionality and register with FastMCP server
        wrapped_handler = self._wrap_tool_handler(name, handler)
        self.mcp_server.add_tool(
            fn=wrapped_handler,
            name=name,
            description=description
        )
    
    def _setup_mcp_handlers(self):
        """Set up MCP message handlers."""
        # FastMCP handles tool calls automatically through registered functions
        # No additional setup needed
        pass
    
    def _wrap_tool_handler(self, tool_name: str, handler: Callable):
        """Wrap a tool handler to add standard functionality."""
        async def wrapped_handler(**kwargs):
            self.request_count += 1
            start_time = datetime.utcnow()
            
            try:
                # Track API usage if this involves external calls  
                await self._track_tool_usage(tool_name, kwargs)
                
                # Analyze conversation for patterns
                if "query" in kwargs or "context" in kwargs:
                    content = kwargs.get("query", kwargs.get("context", ""))
                    await self.pattern_service.analyze_conversation(
                        content, self.domain_name, self.current_session_id or "default"
                    )
                
                # Execute tool handler
                result = await handler(kwargs)
                
                # Cache result if appropriate
                await self._cache_tool_result(tool_name, kwargs, result)
                
                # Update knowledge base
                await self._update_knowledge_from_tool_result(tool_name, kwargs, result)
                
                return result
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Tool call error in {self.server_name}: {e}")
                raise
            
            finally:
                # Log performance
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(f"Tool {tool_name} completed in {duration:.2f}s")
        
        return wrapped_handler
    
    async def _track_tool_usage(self, tool_name: str, arguments: Dict[str, Any]):
        """Track tool usage for cost management."""
        # Estimate token usage based on tool and arguments
        estimated_input_tokens = len(json.dumps(arguments)) // 4  # Rough estimate
        estimated_output_tokens = 100  # Default estimate
        
        await self.cost_service.track_api_usage(
            server_name=self.server_name,
            provider="internal",  # Internal tool usage
            model="tool-call",
            endpoint=tool_name,
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            metadata={"tool_name": tool_name, "domain": self.domain_name}
        )
    
    async def _cache_tool_result(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any], 
        result: Any
    ):
        """Cache tool results for performance."""
        # Generate cache key based on tool and arguments
        cache_key = f"{tool_name}:{hash(json.dumps(arguments, sort_keys=True))}"
        
        # Determine cross-domain relevance
        cross_domain_relevance = []
        if "search" in tool_name or "knowledge" in tool_name:
            cross_domain_relevance = ["financial", "family", "lifestyle", "professional", "home"]
        
        await self.cache_service.set(
            key=cache_key,
            value=result,
            domain=self.domain_name,
            ttl=1800,  # 30 minutes
            cross_domain_relevance=cross_domain_relevance
        )
    
    async def _update_knowledge_from_tool_result(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any
    ):
        """Update knowledge base with tool results."""
        if not isinstance(result, (dict, str)) or len(str(result)) < 50:
            return  # Skip small or non-informative results
        
        # Extract keywords from arguments and result
        keywords = []
        for key, value in arguments.items():
            if isinstance(value, str):
                keywords.extend(value.lower().split())
        
        keywords.extend([tool_name, self.domain_name])
        
        # Store in knowledge base
        await self.db_service.store_knowledge(
            domain=self.domain_name,
            title=f"Tool Result: {tool_name}",
            content=json.dumps(result) if isinstance(result, dict) else str(result),
            metadata={
                "tool_name": tool_name,
                "arguments": arguments,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "tool_result"
            },
            keywords=list(set(keywords))
        )
    
    # Standard tool handlers
    async def _handle_knowledge_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle knowledge search requests."""
        query = arguments["query"]
        domains = arguments.get("domains", [self.domain_name])
        limit = arguments.get("limit", 10)
        
        # Extract keywords from query
        keywords = query.lower().split()
        
        results = await self.db_service.search_knowledge(
            domains=domains,
            keywords=keywords,
            limit=limit
        )
        
        return {
            "query": query,
            "domains_searched": domains,
            "results_count": len(results),
            "results": results
        }
    
    async def _handle_pattern_insights(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern insight requests."""
        context = arguments["context"]
        
        # Get pattern suggestions
        suggestions = await self.pattern_service.get_pattern_suggestions(
            current_domain=self.domain_name,
            session_context=self.session_context
        )
        
        # Get cross-domain cache suggestions
        cache_suggestions = await self.cache_service.get_cross_domain_suggestions(
            current_domain=self.domain_name
        )
        
        return {
            "context": context,
            "pattern_suggestions": suggestions,
            "cross_domain_insights": cache_suggestions,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_session_update(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session context updates."""
        context_update = arguments["context_update"]
        conversation_entry = arguments.get("conversation_entry")
        
        # Update local session context
        self.session_context.update(context_update)
        
        # Update database session
        if not self.current_session_id:
            self.current_session_id = await self.db_service.start_user_session(
                user_id="claude_user",  # Could be made configurable
                initial_context=self.session_context
            )
        else:
            await self.db_service.update_session_context(
                session_id=self.current_session_id,
                context_update=context_update,
                conversation_entry=conversation_entry
            )
        
        return {
            "session_id": self.current_session_id,
            "context_updated": True,
            "active_domains": list(self.session_context.get("active_domains", [self.domain_name]))
        }
    
    async def _handle_usage_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle usage statistics requests."""
        period = arguments.get("period", "daily")
        
        if period == "daily":
            stats = await self.cost_service.get_daily_usage(self.server_name)
        elif period == "weekly":
            stats = await self.cost_service.get_weekly_usage(self.server_name)
        else:  # monthly
            stats = await self.cost_service.get_monthly_usage(self.server_name)
        
        # Add server-specific stats
        stats.update({
            "server_name": self.server_name,
            "domain": self.domain_name,
            "requests_handled": self.request_count,
            "errors": self.error_count,
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "cache_stats": await self.cache_service.get_cache_stats()
        })
        
        return stats
    
    async def start_session(self, user_context: Dict[str, Any] = None):
        """Start a new user session."""
        user_context = user_context or {}
        user_context["domain"] = self.domain_name
        user_context["server_name"] = self.server_name
        
        self.current_session_id = await self.db_service.start_user_session(
            user_id=user_context.get("user_id", "claude_user"),
            initial_context=user_context
        )
        
        self.session_context = user_context
        
        logger.info(f"Started session {self.current_session_id} for {self.server_name}")
        return self.current_session_id
    
    async def end_session(self):
        """End the current session."""
        if self.current_session_id:
            await self.db_service.end_user_session(self.current_session_id)
            logger.info(f"Ended session {self.current_session_id} for {self.server_name}")
            self.current_session_id = None
            self.session_context = {}
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.end_session()
        await self.cache_service.close()
        logger.info(f"Cleaned up {self.server_name}")
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive server status."""
        return {
            "server_name": self.server_name,
            "domain": self.domain_name,
            "status": "running",
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "requests_handled": self.request_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "registered_tools": list(self.tools.keys()),
            "current_session": self.current_session_id,
            "cache_stats": await self.cache_service.get_cache_stats(),
            "pattern_analytics": self.pattern_service.get_pattern_analytics()
        }