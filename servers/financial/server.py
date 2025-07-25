#!/usr/bin/env python3
"""
Financial MCP Server - Domain-specific financial planning and analysis tools.
"""
import asyncio
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

from shared.base_mcp_server import BaseMCPServer

logger = logging.getLogger(__name__)

class FinancialMCPServer(BaseMCPServer):
    """Financial domain MCP server providing financial planning and analysis tools."""
    
    def __init__(self, **kwargs):
        super().__init__(domain_name="financial", **kwargs)
        
    async def register_domain_tools(self):
        """Register financial-specific tools."""
        
        # Budget analysis tool
        self.register_tool(
            name="analyze_budget",
            description="Analyze budget data and provide insights",
            parameters={
                "type": "object",
                "properties": {
                    "income": {"type": "number", "description": "Monthly income"},
                    "expenses": {
                        "type": "object",
                        "description": "Expense categories with amounts",
                        "additionalProperties": {"type": "number"}
                    },
                    "goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Financial goals"
                    }
                },
                "required": ["income", "expenses"]
            },
            handler=self._handle_budget_analysis
        )
        
        # Investment portfolio analysis
        self.register_tool(
            name="analyze_portfolio",
            description="Analyze investment portfolio and provide recommendations",
            parameters={
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "quantity": {"type": "number"},
                                "cost_basis": {"type": "number"}
                            }
                        }
                    },
                    "risk_tolerance": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"]
                    },
                    "time_horizon": {"type": "integer", "description": "Investment timeline in years"}
                },
                "required": ["holdings"]
            },
            handler=self._handle_portfolio_analysis
        )
        
        # Financial goal planning
        self.register_tool(
            name="plan_financial_goal",
            description="Create a plan to achieve specific financial goals",
            parameters={
                "type": "object",
                "properties": {
                    "goal_type": {
                        "type": "string",
                        "enum": ["retirement", "house", "vacation", "emergency_fund", "education", "other"]
                    },
                    "target_amount": {"type": "number", "description": "Target amount needed"},
                    "current_savings": {"type": "number", "description": "Current amount saved"},
                    "timeline_months": {"type": "integer", "description": "Timeline in months"},
                    "monthly_contribution": {"type": "number", "description": "Monthly contribution ability"}
                },
                "required": ["goal_type", "target_amount", "timeline_months"]
            },
            handler=self._handle_goal_planning
        )
        
        # Debt optimization
        self.register_tool(
            name="optimize_debt_payoff",
            description="Optimize debt payoff strategy",
            parameters={
                "type": "object",
                "properties": {
                    "debts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "balance": {"type": "number"},
                                "interest_rate": {"type": "number"},
                                "minimum_payment": {"type": "number"}
                            }
                        }
                    },
                    "extra_payment": {"type": "number", "description": "Extra monthly amount for debt payoff"},
                    "strategy": {
                        "type": "string",
                        "enum": ["avalanche", "snowball", "hybrid"],
                        "default": "avalanche"
                    }
                },
                "required": ["debts"]
            },
            handler=self._handle_debt_optimization
        )

    async def _handle_budget_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze budget and provide insights."""
        income = arguments["income"]
        expenses = arguments["expenses"]
        goals = arguments.get("goals", [])
        
        total_expenses = sum(expenses.values())
        net_income = income - total_expenses
        savings_rate = (net_income / income) * 100 if income > 0 else 0
        
        # Categorize spending
        spending_analysis = {}
        for category, amount in expenses.items():
            percentage = (amount / income) * 100 if income > 0 else 0
            spending_analysis[category] = {
                "amount": amount,
                "percentage_of_income": round(percentage, 2)
            }
        
        # Budget health assessment
        health_score = min(100, max(0, savings_rate * 2))  # Simple scoring
        
        recommendations = []
        if savings_rate < 10:
            recommendations.append("Consider increasing savings rate to at least 10% of income")
        if savings_rate < 0:
            recommendations.append("URGENT: Expenses exceed income - review and cut costs immediately")
        
        # Check for high expense categories
        for category, data in spending_analysis.items():
            if data["percentage_of_income"] > 30 and category.lower() not in ["housing", "rent"]:
                recommendations.append(f"Consider reducing {category} spending (currently {data['percentage_of_income']:.1f}% of income)")
        
        return {
            "budget_summary": {
                "monthly_income": income,
                "total_expenses": total_expenses,
                "net_income": net_income,
                "savings_rate": round(savings_rate, 2)
            },
            "spending_analysis": spending_analysis,
            "health_score": round(health_score, 1),
            "recommendations": recommendations,
            "goals_assessment": self._assess_goals_feasibility(net_income, goals),
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    async def _handle_portfolio_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze investment portfolio."""
        holdings = arguments["holdings"]
        risk_tolerance = arguments.get("risk_tolerance", "moderate")
        time_horizon = arguments.get("time_horizon", 10)
        
        total_value = sum(h.get("quantity", 0) * h.get("cost_basis", 0) for h in holdings)
        
        # Simple diversification analysis
        portfolio_analysis = {
            "total_holdings": len(holdings),
            "estimated_value": total_value,
            "diversification_score": min(100, len(holdings) * 10),  # Simple scoring
            "risk_assessment": risk_tolerance
        }
        
        recommendations = [
            "Consider regular portfolio rebalancing",
            "Ensure adequate diversification across sectors and asset classes"
        ]
        
        if len(holdings) < 5:
            recommendations.append("Consider adding more holdings for better diversification")
        
        if risk_tolerance == "conservative" and time_horizon > 15:
            recommendations.append("With longer time horizon, consider moderate risk tolerance")
        
        return {
            "portfolio_analysis": portfolio_analysis,
            "recommendations": recommendations,
            "risk_tolerance": risk_tolerance,
            "time_horizon_years": time_horizon,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    async def _handle_goal_planning(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create financial goal achievement plan."""
        goal_type = arguments["goal_type"]
        target_amount = arguments["target_amount"]
        current_savings = arguments.get("current_savings", 0)
        timeline_months = arguments["timeline_months"]
        monthly_contribution = arguments.get("monthly_contribution", 0)
        
        remaining_amount = target_amount - current_savings
        required_monthly_savings = remaining_amount / timeline_months if timeline_months > 0 else 0
        
        # Calculate if goal is achievable
        achievable = monthly_contribution >= required_monthly_savings
        shortfall = max(0, required_monthly_savings - monthly_contribution)
        
        plan = {
            "goal_details": {
                "type": goal_type,
                "target_amount": target_amount,
                "current_savings": current_savings,
                "amount_needed": remaining_amount,
                "timeline_months": timeline_months
            },
            "savings_plan": {
                "required_monthly_savings": round(required_monthly_savings, 2),
                "current_monthly_contribution": monthly_contribution,
                "is_achievable": achievable,
                "monthly_shortfall": round(shortfall, 2) if shortfall > 0 else 0
            },
            "recommendations": []
        }
        
        if not achievable:
            plan["recommendations"].extend([
                f"Increase monthly savings by ${shortfall:.2f} to meet goal",
                f"Or extend timeline by {int((remaining_amount / monthly_contribution) - timeline_months)} months"
            ])
        else:
            plan["recommendations"].append("Goal is achievable with current contribution plan!")
        
        # Add goal-specific advice
        if goal_type == "emergency_fund":
            plan["recommendations"].append("Aim for 3-6 months of expenses for emergency fund")
        elif goal_type == "retirement":
            plan["recommendations"].append("Consider maximizing employer 401(k) matching first")
        
        return plan
    
    async def _handle_debt_optimization(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize debt payoff strategy."""
        debts = arguments["debts"]
        extra_payment = arguments.get("extra_payment", 0)
        strategy = arguments.get("strategy", "avalanche")
        
        total_debt = sum(d["balance"] for d in debts)
        total_minimum = sum(d["minimum_payment"] for d in debts)
        
        # Sort debts by strategy
        if strategy == "avalanche":
            sorted_debts = sorted(debts, key=lambda x: x["interest_rate"], reverse=True)
        elif strategy == "snowball":
            sorted_debts = sorted(debts, key=lambda x: x["balance"])
        else:  # hybrid
            # Sort by interest rate but prioritize small balances under $1000
            def hybrid_key(debt):
                if debt["balance"] < 1000:
                    return -debt["balance"]  # Negative for ascending sort of small debts
                return -debt["interest_rate"]  # Negative for descending sort of interest rates
            sorted_debts = sorted(debts, key=hybrid_key)
        
        # Calculate payoff timeline
        payoff_plan = []
        remaining_extra = extra_payment
        
        for i, debt in enumerate(sorted_debts):
            priority_payment = debt["minimum_payment"]
            if i == 0:  # First debt gets extra payment
                priority_payment += remaining_extra
            
            months_to_payoff = debt["balance"] / priority_payment if priority_payment > 0 else float('inf')
            
            payoff_plan.append({
                "debt_name": debt["name"],
                "balance": debt["balance"],
                "interest_rate": debt["interest_rate"],
                "priority_payment": round(priority_payment, 2),
                "estimated_payoff_months": round(months_to_payoff, 1)
            })
        
        return {
            "debt_summary": {
                "total_debt": total_debt,
                "total_minimum_payments": total_minimum,
                "extra_payment_available": extra_payment,
                "strategy_used": strategy
            },
            "payoff_plan": payoff_plan,
            "recommendations": [
                f"Focus extra payments on {sorted_debts[0]['name']} first",
                "Continue minimum payments on all other debts",
                "Consider debt consolidation if rates can be improved"
            ],
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _assess_goals_feasibility(self, net_income: float, goals: List[str]) -> Dict[str, Any]:
        """Assess feasibility of financial goals."""
        if net_income <= 0:
            return {"feasible": False, "reason": "No surplus income available for goals"}
        
        # Simple goal assessment
        goal_assessment = {
            "surplus_available": net_income,
            "feasible": net_income > 0,
            "recommended_allocation": {
                "emergency_fund": round(net_income * 0.3, 2),
                "retirement": round(net_income * 0.4, 2),
                "other_goals": round(net_income * 0.3, 2)
            }
        }
        
        return goal_assessment

async def main():
    """Main function to run the Financial MCP Server."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    budget_limit = float(os.getenv("FINANCIAL_BUDGET_LIMIT", "15.0"))
    
    # Create and initialize server
    server = FinancialMCPServer(
        database_url=database_url,
        redis_url=redis_url,
        daily_budget_limit=budget_limit
    )
    
    try:
        await server.initialize()
        logger.info(f"Financial MCP Server initialized with {len(server.tools)} tools")
        
        # Keep server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Financial MCP Server shutting down...")
    except Exception as e:
        logger.error(f"Financial MCP Server error: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())