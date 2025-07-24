"""
PatternRecognitionService for cross-domain intelligence and pattern detection.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import json
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Pattern:
    """Represents a detected pattern across domains."""
    name: str
    domains: List[str]
    triggers: List[str]
    confidence: float
    frequency: int
    last_seen: datetime
    metadata: Dict[str, Any]

class PatternRecognitionService:
    """Service for detecting and managing cross-domain patterns."""
    
    def __init__(self, database_service):
        self.db = database_service
        self.pattern_cache = {}
        self.trigger_history = defaultdict(list)
        self.pattern_templates = self._initialize_pattern_templates()
        
    def _initialize_pattern_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common pattern templates for recognition."""
        return {
            'financial_planning_event': {
                'triggers': ['budget', 'expense', 'investment', 'savings', 'financial goal'],
                'domains': ['financial', 'family', 'lifestyle'],
                'conditions': {
                    'time_window': timedelta(hours=24),
                    'min_domains': 2,
                    'confidence_threshold': 0.7
                }
            },
            'home_improvement_project': {
                'triggers': ['renovation', 'repair', 'improvement', 'maintenance', 'contractor'],
                'domains': ['home', 'financial', 'family'],
                'conditions': {
                    'time_window': timedelta(days=7),
                    'min_domains': 2,
                    'confidence_threshold': 0.6
                }
            },
            'family_activity_planning': {
                'triggers': ['vacation', 'trip', 'event', 'celebration', 'activity'],
                'domains': ['family', 'financial', 'lifestyle'],
                'conditions': {
                    'time_window': timedelta(days=3),
                    'min_domains': 2,
                    'confidence_threshold': 0.8
                }
            },
            'career_development': {
                'triggers': ['promotion', 'job', 'career', 'skill', 'training', 'certification'],
                'domains': ['professional', 'financial', 'lifestyle'],
                'conditions': {
                    'time_window': timedelta(days=14),
                    'min_domains': 2,
                    'confidence_threshold': 0.7
                }
            },
            'health_lifestyle_change': {
                'triggers': ['health', 'fitness', 'diet', 'exercise', 'wellness'],
                'domains': ['lifestyle', 'family', 'financial'],
                'conditions': {
                    'time_window': timedelta(days=5),
                    'min_domains': 2,
                    'confidence_threshold': 0.6
                }
            }
        }
    
    async def analyze_conversation(
        self, 
        content: str, 
        domain: str, 
        session_id: str,
        metadata: Dict[str, Any] = None
    ) -> List[Pattern]:
        """Analyze conversation content for pattern triggers."""
        metadata = metadata or {}
        
        # Extract triggers from content
        triggers = self._extract_triggers(content)
        
        # Record trigger occurrence
        self.trigger_history[session_id].append({
            'domain': domain,
            'triggers': triggers,
            'timestamp': datetime.utcnow(),
            'content_summary': content[:200] + '...' if len(content) > 200 else content,
            'metadata': metadata
        })
        
        # Detect patterns
        detected_patterns = await self._detect_patterns(session_id)
        
        # Store significant patterns
        for pattern in detected_patterns:
            if pattern.confidence >= 0.6:
                await self._store_pattern(pattern, session_id)
        
        return detected_patterns
    
    def _extract_triggers(self, content: str) -> List[str]:
        """Extract trigger keywords from content."""
        content_lower = content.lower()
        triggers = []
        
        for template_name, template in self.pattern_templates.items():
            for trigger in template['triggers']:
                if trigger in content_lower:
                    triggers.append(trigger)
        
        # Custom trigger extraction using regex
        financial_patterns = [
            r'\$[\d,]+', r'budget.*\d+', r'cost.*\d+', r'expense.*\d+', 
            r'invest.*\d+', r'save.*\d+'
        ]
        
        for pattern in financial_patterns:
            if re.search(pattern, content_lower):
                triggers.append('financial_amount')
        
        return list(set(triggers))
    
    async def _detect_patterns(self, session_id: str) -> List[Pattern]:
        """Detect patterns from trigger history."""
        history = self.trigger_history[session_id]
        detected_patterns = []
        
        for template_name, template in self.pattern_templates.items():
            pattern = await self._check_pattern_template(
                template_name, template, history
            )
            if pattern:
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    async def _check_pattern_template(
        self, 
        template_name: str, 
        template: Dict[str, Any], 
        history: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """Check if a pattern template matches recent history."""
        time_window = template['conditions']['time_window']
        min_domains = template['conditions']['min_domains']
        confidence_threshold = template['conditions']['confidence_threshold']
        
        # Filter recent history within time window
        cutoff_time = datetime.utcnow() - time_window
        recent_history = [
            entry for entry in history 
            if entry['timestamp'] >= cutoff_time
        ]
        
        if not recent_history:
            return None
        
        # Check for trigger matches and domain coverage
        triggered_domains = set()
        matched_triggers = []
        
        for entry in recent_history:
            entry_triggers = set(entry['triggers'])
            template_triggers = set(template['triggers'])
            
            if entry_triggers.intersection(template_triggers):
                triggered_domains.add(entry['domain'])
                matched_triggers.extend(list(entry_triggers.intersection(template_triggers)))
        
        # Calculate confidence based on trigger frequency and domain coverage
        trigger_frequency = len(matched_triggers)
        domain_coverage = len(triggered_domains)
        
        if domain_coverage < min_domains:
            return None
        
        # Confidence calculation
        max_possible_domains = len(template['domains'])
        domain_score = min(domain_coverage / max_possible_domains, 1.0)
        trigger_score = min(trigger_frequency / len(template['triggers']), 1.0)
        
        confidence = (domain_score * 0.6) + (trigger_score * 0.4)
        
        if confidence < confidence_threshold:
            return None
        
        return Pattern(
            name=template_name,
            domains=list(triggered_domains),
            triggers=list(set(matched_triggers)),
            confidence=confidence,
            frequency=trigger_frequency,
            last_seen=max(entry['timestamp'] for entry in recent_history),
            metadata={
                'template': template_name,
                'recent_entries': len(recent_history),
                'time_window_hours': time_window.total_seconds() / 3600
            }
        )
    
    async def _store_pattern(self, pattern: Pattern, session_id: str):
        """Store detected pattern in database."""
        pattern_data = {
            'triggers': pattern.triggers,
            'session_id': session_id,
            'frequency': pattern.frequency,
            'last_seen': pattern.last_seen.isoformat(),
            'metadata': pattern.metadata
        }
        
        await self.db.store_cross_domain_pattern(
            pattern_name=pattern.name,
            pattern_data=pattern_data,
            involved_domains=pattern.domains,
            confidence_score=pattern.confidence
        )
    
    async def get_pattern_suggestions(
        self, 
        current_domain: str, 
        session_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get pattern-based suggestions for the current context."""
        suggestions = []
        
        # Get recent patterns involving current domain
        relevant_patterns = await self.db.get_relevant_patterns(
            domains=[current_domain],
            min_confidence=0.6
        )
        
        for pattern_data in relevant_patterns:
            pattern_name = pattern_data['pattern_name']
            involved_domains = pattern_data['involved_domains']
            
            # Generate suggestions based on pattern
            pattern_suggestions = self._generate_pattern_suggestions(
                pattern_name, involved_domains, current_domain, session_context
            )
            suggestions.extend(pattern_suggestions)
        
        return suggestions
    
    def _generate_pattern_suggestions(
        self, 
        pattern_name: str, 
        involved_domains: List[str], 
        current_domain: str,
        session_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate specific suggestions based on detected pattern."""
        suggestions = []
        
        if pattern_name == 'financial_planning_event':
            if current_domain == 'financial':
                suggestions.append({
                    'type': 'cross_domain_insight',
                    'message': 'Consider how this financial decision affects family plans and lifestyle goals',
                    'related_domains': ['family', 'lifestyle'],
                    'confidence': 0.8
                })
            elif current_domain == 'family':
                suggestions.append({
                    'type': 'budget_check',
                    'message': 'Review budget impact of family activities and events',
                    'related_domains': ['financial'],
                    'confidence': 0.7
                })
        
        elif pattern_name == 'home_improvement_project':
            if current_domain == 'home':
                suggestions.append({
                    'type': 'financial_planning',
                    'message': 'Create budget and timeline for home improvement project',
                    'related_domains': ['financial'],
                    'confidence': 0.9
                })
            elif current_domain == 'financial':
                suggestions.append({
                    'type': 'project_coordination',
                    'message': 'Coordinate home project costs with family schedule',
                    'related_domains': ['home', 'family'],
                    'confidence': 0.8
                })
        
        elif pattern_name == 'family_activity_planning':
            if current_domain == 'family':
                suggestions.append({
                    'type': 'budget_planning',
                    'message': 'Plan budget for upcoming family activities and events',
                    'related_domains': ['financial'],
                    'confidence': 0.8
                })
            elif current_domain == 'lifestyle':
                suggestions.append({
                    'type': 'schedule_integration',
                    'message': 'Integrate family activities with personal lifestyle goals',
                    'related_domains': ['family'],
                    'confidence': 0.7
                })
        
        return suggestions
    
    async def cleanup_old_patterns(self, days_old: int = 30):
        """Clean up old patterns and trigger history."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Clean up trigger history
        for session_id, history in list(self.trigger_history.items()):
            self.trigger_history[session_id] = [
                entry for entry in history 
                if entry['timestamp'] >= cutoff_date
            ]
            if not self.trigger_history[session_id]:
                del self.trigger_history[session_id]
        
        logger.info(f"Cleaned up pattern data older than {days_old} days")
    
    def get_pattern_analytics(self) -> Dict[str, Any]:
        """Get analytics about pattern detection."""
        total_sessions = len(self.trigger_history)
        total_triggers = sum(
            len(history) for history in self.trigger_history.values()
        )
        
        # Count patterns by type
        pattern_counts = Counter()
        for history in self.trigger_history.values():
            for entry in history:
                for trigger in entry['triggers']:
                    pattern_counts[trigger] += 1
        
        return {
            'total_sessions': total_sessions,
            'total_triggers': total_triggers,
            'most_common_triggers': pattern_counts.most_common(10),
            'pattern_templates': list(self.pattern_templates.keys()),
            'cache_size': len(self.pattern_cache)
        }