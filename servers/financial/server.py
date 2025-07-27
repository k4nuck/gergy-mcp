#!/usr/bin/env python3
"""
Financial MCP Server - Domain-specific financial planning and analysis tools.
"""
import asyncio
import logging
import os
import ssl
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
import uvicorn
import json

from shared.base_mcp_server import BaseMCPServer

logger = logging.getLogger(__name__)

# Configuration constants
MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = os.getenv("DOMAIN_NAME", "financial")
SERVER_FULL_NAME = f"gergy-{SERVER_NAME}"

class FinancialMCPServer(BaseMCPServer):
    """Financial domain MCP server providing financial planning and analysis tools."""
    
    def __init__(self, **kwargs):
        super().__init__(domain_name="financial", **kwargs)
        
    async def register_domain_tools(self):
        """Register financial-specific tools."""
        
        # Financial context retrieval tool
        self.register_tool(
            name="retrieve_financial_context",
            description="Retrieve relevant financial data based on structured query parameters",
            parameters={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "Type of financial query",
                        "enum": ["expense_analysis", "budget_planning", "goal_tracking", "account_summary", "transaction_history", "investment_review"]
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific financial categories to include (e.g., travel, dining, housing)"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Time period for data retrieval",
                        "enum": ["current_month", "last_month", "last_3_months", "last_6_months", "last_year", "ytd", "all_time"]
                    },
                    "amount_range": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"}
                        },
                        "description": "Optional amount range filter"
                    },
                    "accounts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific accounts to include"
                    }
                },
                "required": ["query_type"]
            },
            handler=self._handle_context_retrieval
        )
        
        # Store financial data tool
        self.register_tool(
            name="store_financial_data",
            description="Store financial information with support for explicit commands and conversational context",
            parameters={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of financial data",
                        "enum": ["transaction", "account_balance", "goal", "budget_item", "investment_holding", "debt_balance", "income", "recurring_expense"]
                    },
                    "data": {
                        "type": "object",
                        "description": "The financial data to store",
                        "properties": {
                            "amount": {"type": "number", "description": "Monetary amount (positive for income/assets, negative for expenses)"},
                            "account": {"type": "string", "description": "Account name (checking, savings, credit_card, etc.)"},
                            "category": {"type": "string", "description": "Category (groceries, dining, salary, etc.)"},
                            "description": {"type": "string", "description": "Description or notes"},
                            "date": {"type": "string", "format": "date", "description": "Transaction or record date"},
                            "merchant": {"type": "string", "description": "Merchant or source"},
                            "recurring": {"type": "boolean", "description": "Whether this is a recurring item"}
                        }
                    },
                    "update_method": {
                        "type": "string",
                        "description": "How this data was obtained",
                        "enum": ["explicit", "conversational", "imported", "calculated"],
                        "default": "explicit"
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "Confidence in the data accuracy (0.0-1.0, higher is more confident)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 1.0
                    },
                    "source_context": {
                        "type": "string",
                        "description": "Original user statement or context that generated this data"
                    }
                },
                "required": ["data_type", "data"]
            },
            handler=self._handle_data_storage
        )
        
        # Financial summary tool
        self.register_tool(
            name="get_financial_summary",
            description="Get current financial snapshot with account balances, recent activity, and key metrics",
            parameters={
                "type": "object",
                "properties": {
                    "include_accounts": {
                        "type": "boolean",
                        "description": "Include account balances",
                        "default": True
                    },
                    "include_recent_activity": {
                        "type": "boolean",
                        "description": "Include recent transactions",
                        "default": True
                    },
                    "include_goals": {
                        "type": "boolean",
                        "description": "Include financial goals status",
                        "default": True
                    }
                }
            },
            handler=self._handle_financial_summary
        )
        
        # Search financial history tool
        self.register_tool(
            name="search_financial_history",
            description="Search historical financial data with flexible filters",
            parameters={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Text to search for in descriptions, categories, or notes"
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"}
                        }
                    },
                    "transaction_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of transactions to include (income, expense, transfer, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 50
                    }
                }
            },
            handler=self._handle_history_search
        )

    async def _handle_context_retrieval(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant financial data based on query parameters."""
        query_type = arguments["query_type"]
        categories = arguments.get("categories", [])
        timeframe = arguments.get("timeframe", "current_month")
        amount_range = arguments.get("amount_range")
        accounts = arguments.get("accounts", [])
        
        # Use database service to retrieve relevant financial data
        search_filters = {
            "domain": "financial",
            "keywords": categories,
        }
        
        # Add timeframe filtering logic here
        if timeframe != "all_time":
            search_filters["metadata"] = {"timeframe": timeframe}
        
        # Retrieve data from database
        financial_data = await self.db_service.search_knowledge(
            query=f"{query_type} {' '.join(categories)}",
            **search_filters
        )
        
        # Format response with raw data
        return {
            "query_type": query_type,
            "filters_applied": {
                "categories": categories,
                "timeframe": timeframe,
                "amount_range": amount_range,
                "accounts": accounts
            },
            "data": financial_data,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_data_storage(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Store financial data with enhanced metadata tracking."""
        data_type = arguments["data_type"]
        data = arguments["data"]
        update_method = arguments.get("update_method", "explicit")
        confidence_score = arguments.get("confidence_score", 1.0)
        source_context = arguments.get("source_context", "")
        
        # Build comprehensive metadata
        metadata = {
            "data_type": data_type,
            "update_method": update_method,
            "confidence_score": confidence_score,
            "stored_at": datetime.utcnow().isoformat(),
        }
        
        if source_context:
            metadata["source_context"] = source_context
            
        # Add financial-specific metadata
        if "account" in data:
            metadata["account"] = data["account"]
        if "category" in data:
            metadata["category"] = data["category"]
        if "date" in data:
            metadata["transaction_date"] = data["date"]
        if "amount" in data:
            metadata["amount"] = data["amount"]
            metadata["amount_type"] = "income" if data["amount"] > 0 else "expense"
            
        # Build keywords for search
        keywords = [data_type, update_method]
        if isinstance(data, dict):
            keywords.extend([k for k in data.keys() if isinstance(data[k], str)])
            if "category" in data:
                keywords.append(data["category"])
            if "merchant" in data:
                keywords.append(data["merchant"])
        
        # Generate descriptive title
        title = self._generate_data_title(data_type, data)
        
        # Store in database using the knowledge storage system
        result = await self.db_service.store_knowledge(
            domain="financial",
            title=title,
            content=str(data),  # Convert to string for storage
            content_type="financial_data",
            metadata=metadata,
            keywords=keywords
        )
        
        return {
            "status": "stored",
            "data_type": data_type,
            "record_id": result,
            "update_method": update_method,
            "confidence_score": confidence_score,
            "stored_at": metadata["stored_at"],
            "title": title
        }
    
    def _generate_data_title(self, data_type: str, data: Dict[str, Any]) -> str:
        """Generate a descriptive title for the financial data."""
        if data_type == "transaction":
            amount = data.get("amount", 0)
            category = data.get("category", "Unknown")
            merchant = data.get("merchant", "")
            if merchant:
                return f"{category} - ${abs(amount):.2f} at {merchant}"
            else:
                return f"{category} - ${abs(amount):.2f}"
        elif data_type == "account_balance":
            account = data.get("account", "Unknown Account")
            balance = data.get("amount", 0)
            return f"{account} Balance: ${balance:.2f}"
        elif data_type == "goal":
            description = data.get("description", "Financial Goal")
            amount = data.get("amount", 0)
            return f"Goal: {description} (${amount:.2f})"
        else:
            return f"{data_type.replace('_', ' ').title()}"
    
    async def _handle_financial_summary(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get current financial snapshot."""
        include_accounts = arguments.get("include_accounts", True)
        include_recent_activity = arguments.get("include_recent_activity", True)
        include_goals = arguments.get("include_goals", True)
        
        summary = {
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if include_accounts:
            # Retrieve account data
            account_data = await self.db_service.search_knowledge(
                query="accounts balances",
                domain="financial",
                keywords=["account", "balance"]
            )
            summary["accounts"] = account_data
        
        if include_recent_activity:
            # Retrieve recent transactions
            recent_data = await self.db_service.search_knowledge(
                query="recent transactions",
                domain="financial",
                keywords=["transaction", "recent"]
            )
            summary["recent_activity"] = recent_data
        
        if include_goals:
            # Retrieve financial goals
            goal_data = await self.db_service.search_knowledge(
                query="financial goals",
                domain="financial",
                keywords=["goal", "target"]
            )
            summary["goals"] = goal_data
        
        return summary
    
    async def _handle_history_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search historical financial data."""
        search_term = arguments.get("search_term", "")
        date_range = arguments.get("date_range")
        transaction_types = arguments.get("transaction_types", [])
        limit = arguments.get("limit", 50)
        
        # Build search keywords
        keywords = transaction_types.copy()
        if search_term:
            keywords.extend(search_term.split())
        
        # Search financial history
        results = await self.db_service.search_knowledge(
            query=search_term or "financial history",
            domain="financial",
            keywords=keywords
        )
        
        # Apply limit
        if len(results) > limit:
            results = results[:limit]
        
        return {
            "search_parameters": {
                "search_term": search_term,
                "date_range": date_range,
                "transaction_types": transaction_types,
                "limit": limit
            },
            "results": results,
            "total_found": len(results),
            "searched_at": datetime.utcnow().isoformat()
        }
    

# Global server instance
mcp_server = None

# FastAPI app for HTTPS endpoints
app = FastAPI(title="Gergy Financial MCP Server", description="HTTPS endpoints for MCP tools")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://claude.ai",
        "https://*.claude.ai", 
        "https://claude.anthropic.com",
        "https://*.anthropic.com",
        "*"  # Fallback for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "Accept", 
        "Origin", 
        "X-Requested-With",
        "Cache-Control",
        "X-MCP-Version"
    ],
)

# Add MCP-specific response headers and detailed logging
@app.middleware("http")
async def add_mcp_headers(request, call_next):
    # Log all incoming requests with details
    client_ip = request.client.host if request.client else "unknown"
    origin = request.headers.get("origin", "none")
    user_agent = request.headers.get("user-agent", "none")
    auth_header = request.headers.get("authorization", "none")
    
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip} | Origin: {origin} | User-Agent: {user_agent[:50]}... | Auth: {auth_header[:20]}...")
    
    # Handle CORS preflight requests globally
    if request.method == "OPTIONS":
        return Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "false",
                "Access-Control-Max-Age": "86400"
            }
        )
    
    response = await call_next(request)
    # Add CORS headers to all responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["X-MCP-Version"] = MCP_PROTOCOL_VERSION
    response.headers["X-MCP-Transport"] = "http"
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.on_event("startup")
async def startup():
    """Initialize MCP server on FastAPI startup."""
    global mcp_server
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    budget_limit = float(os.getenv("FINANCIAL_BUDGET_LIMIT", "15.0"))
    
    mcp_server = FinancialMCPServer(
        database_url=database_url,
        redis_url=redis_url,
        daily_budget_limit=budget_limit
    )
    
    await mcp_server.initialize()
    logger.info(f"Financial MCP Server initialized with {len(mcp_server.tools)} tools")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "server": "Gergy Financial MCP Server",
        "tools": len(mcp_server.tools) if mcp_server else 0
    }

@app.options("/mcp/initialize")
async def mcp_initialize_options():
    """Handle CORS preflight for initialize endpoint."""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept"
        }
    )

@app.get("/financial/mcp/initialize")
async def mcp_initialize():
    """MCP protocol initialization handshake."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return Response(
        content=json.dumps({
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "subscribe": True,
                    "listChanged": True
                },
                "prompts": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": SERVER_FULL_NAME,
                "version": "1.0.0",
                "description": "Gergy Financial MCP Server - Personal financial data management with 8 tools for transactions, balances, and insights"
            }
        }),
        media_type="application/json",
        headers={
            "X-MCP-Auth": "none",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.options("/financial/mcp/tools/list")
async def mcp_list_tools_options():
    """Handle CORS preflight for tools list endpoint."""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept"
        }
    )

@app.get("/financial/mcp/tools/list")
async def mcp_list_tools():
    """MCP protocol tool discovery."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters
            }
            for tool in mcp_server.tools.values()
        ]
    }

@app.options("/mcp/tools/call")
async def mcp_call_tool_options():
    """Handle CORS preflight for tool call endpoint."""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept"
        }
    )

@app.post("/financial/mcp/tools/call")
async def mcp_call_tool(request: Dict[str, Any]):
    """MCP protocol tool execution."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="Tool name required")
    
    if tool_name not in mcp_server.tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        tool = mcp_server.tools[tool_name]
        result = await tool.handler(arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def list_tools():
    """REST API: List available MCP tools."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in mcp_server.tools.values()
        ]
    }

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, parameters: Dict[str, Any]):
    """Call an MCP tool."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    if tool_name not in mcp_server.tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        tool = mcp_server.tools[tool_name]
        result = await tool.handler(parameters)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# No authentication required for Claude.ai Pro MCP - just proper CORS

@app.options("/mcp/sse")
async def mcp_sse_options():
    """Handle CORS preflight for SSE endpoint."""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "false",
            "Access-Control-Max-Age": "86400"
        }
    )

# Backward compatibility - redirect old endpoint to new one
@app.get("/mcp/sse")
@app.post("/mcp/sse")
@app.head("/mcp/sse")
async def mcp_sse_legacy(request: Request):
    """Legacy MCP SSE endpoint - redirects to /financial/mcp/sse for backward compatibility."""
    return await mcp_sse(request)

@app.get("/financial/mcp/sse")
@app.post("/financial/mcp/sse")
@app.head("/financial/mcp/sse")
async def mcp_sse(request: Request):
    """MCP Server-Sent Events endpoint for real-time communication."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    # Handle POST body data if present
    post_data = None
    if request.method == "POST":
        try:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                post_data = await request.json()
                logger.info(f"MCP SSE POST data: {post_data}")
            elif content_type:
                body = await request.body()
                if body:
                    logger.info(f"MCP SSE POST body: {body.decode('utf-8', errors='ignore')[:200]}...")
        except Exception as e:
            logger.warning(f"Failed to parse POST data: {e}")
    
    # Log the request for debugging
    origin = request.headers.get("origin", "unknown")
    user_agent = request.headers.get("user-agent", "unknown")
    logger.info(f"MCP SSE connection from origin: {origin}, user-agent: {user_agent}, method: {request.method}")
    
    async def event_stream():
        import asyncio
        
        try:
            # Extract method and request ID from POST data
            method = "initialize"  # default for GET requests
            request_id = 0
            
            if post_data:
                method = post_data.get("method", "initialize")
                request_id = post_data.get("id", 0)
                logger.info(f"Processing MCP method: {method} (ID: {request_id})")
            
            # Handle different MCP methods
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            },
                            "resources": {
                                "subscribe": True,
                                "listChanged": True
                            },
                            "prompts": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": SERVER_FULL_NAME,
                            "version": "1.0.0",
                            "description": "Gergy Financial MCP Server"
                        }
                    }
                }
                
            elif method == "tools/list":
                tools_data = []
                for tool in mcp_server.tools.values():
                    tools_data.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.parameters
                    })
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools_data
                    }
                }
                
            elif method == "prompts/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "prompts": []  # No prompts supported
                    }
                }
                
            elif method == "resources/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "resources": []  # No resources supported
                    }
                }
                
            elif method == "tools/call":
                # Handle tool execution
                try:
                    params = post_data.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if not tool_name:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32602,
                                "message": "Invalid params: missing tool name"
                            }
                        }
                    elif tool_name not in mcp_server.tools:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}"
                            }
                        }
                    else:
                        # Execute the tool
                        tool = mcp_server.tools[tool_name]
                        tool_result = await tool.handler(arguments)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                                    }
                                ]
                            }
                        }
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                
            elif method == "notifications/initialized":
                # This is a notification (no response required, but we'll acknowledge)
                logger.info("Client initialization completed")
                response = None  # Notifications don't require responses
                
            else:
                # Unknown method - return error
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Send the specific response (if any - notifications don't require responses)
            if response is not None:
                response_data = f"data: {json.dumps(response)}\n\n"
                logger.info(f"SSE RESPONSE for {method}: {response_data[:500]}..." if len(response_data) > 500 else f"SSE RESPONSE for {method}: {response_data.strip()}")
                yield response_data
            else:
                logger.info(f"No response required for notification: {method}")
                # For notifications, just send a minimal acknowledgment to keep connection alive
                yield "data: \n\n"
            
            # For GET requests (streaming), send periodic pings to keep connection alive
            if request.method == "GET":
                while True:
                    await asyncio.sleep(30)
                    ping_message = {
                        "jsonrpc": "2.0",
                        "method": "ping",
                        "params": {
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                    ping_data = f"data: {json.dumps(ping_message)}\n\n"
                    logger.info(f"SSE PING: {ping_data.strip()}")
                    yield ping_data
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            error_message = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            error_data = f"data: {json.dumps(error_message)}\n\n"
            logger.error(f"SSE ERROR: {error_data.strip()}")
            yield error_data
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-MCP-Transport": "sse",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "false",
            "Access-Control-Expose-Headers": "*"
        }
    )

def get_ssl_cert_paths():
    """Get SSL certificate and key paths."""
    import os
    
    # Use No-IP certificate if available (container path)
    cert_dir = "/app/certs"
    noip_cert = f"{cert_dir}/cert.pem"
    noip_key = f"{cert_dir}/key.pem"
    
    if os.path.exists(noip_cert) and os.path.exists(noip_key):
        logger.info("Using No-IP SSL certificate for k4nuckhome.hopto.org")
        return noip_cert, noip_key
    
    # Fallback to self-signed certificate
    logger.warning("No-IP certificate not found, creating self-signed certificate")
    return create_self_signed_cert()

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS (fallback only)."""
    import subprocess
    import os
    
    cert_dir = "/tmp/certs"
    os.makedirs(cert_dir, exist_ok=True)
    
    cert_file = f"{cert_dir}/cert.pem"
    key_file = f"{cert_dir}/key.pem"
    
    # Always regenerate for testing
    if os.path.exists(cert_file):
        os.remove(cert_file)
    if os.path.exists(key_file):
        os.remove(key_file)
    
    # Simple self-signed certificate that works with Claude.ai
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:4096", "-nodes",
        "-out", cert_file, "-keyout", key_file, "-days", "365",
        "-subj", "/CN=k4nuckhome.hopto.org"
    ], check=True)
    
    return cert_file, key_file

async def main():
    """Main function to run the Financial MCP Server."""
    
    # Check if we should run in HTTPS mode
    https_mode = os.getenv("HTTPS_MODE", "true").lower() == "true"
    port = int(os.getenv("PORT", "8000"))
    
    if https_mode:
        try:
            cert_file, key_file = get_ssl_cert_paths()
            logger.info(f"Starting Financial MCP Server with HTTPS on port {port}")
            
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_file, key_file)
            
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=port,
                ssl_keyfile=key_file,
                ssl_certfile=cert_file,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"HTTPS setup failed: {e}")
            logger.info("Falling back to HTTP mode")
            https_mode = False
    
    if not https_mode:
        logger.info(f"Starting Financial MCP Server with HTTP on port {port}")
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())