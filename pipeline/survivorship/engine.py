"""
GoldenRecord Survivorship Policy Engine
Defines attribute-level survivorship rules with full metadata capture
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class SurvivorshipRule:
    """Base class for survivorship rules"""

    def apply(self, values: List[Dict[str, Any]]) -> Tuple[Any, Dict[str, Any]]:
        """
        Apply the rule to select the best value.
        Returns: (selected_value, decision_metadata)
        """
        raise NotImplementedError


class MostRecentRule(SurvivorshipRule):
    """Select the most recently updated value"""

    def apply(self, values: List[Dict[str, Any]]) -> Tuple[Any, Dict[str, Any]]:
        if not values:
            return None, {'rule': 'most_recent', 'rationale': 'No values available'}

        # Sort by updated_at descending
        sorted_vals = sorted(
            [v for v in values if v.get('updated_at')],
            key=lambda x: x.get('updated_at', ''),
            reverse=True
        )

        if sorted_vals:
            winner = sorted_vals[0]
            rejected = [
                {'source': v.get('source_system', 'unknown'),
                 'value': v.get('value'),
                 'updated_at': str(v.get('updated_at'))}
                for v in sorted_vals[1:]
            ]
            return winner.get('value'), {
                'rule': 'most_recent',
                'selected_source': winner.get('source_system', 'unknown'),
                'selected_updated_at': str(winner.get('updated_at')),
                'rejected_sources': rejected,
                'rationale': f"Selected most recently updated value from {winner.get('source_system', 'unknown')}"
            }

        # Fallback: first non-null value
        for v in values:
            if v.get('value'):
                return v.get('value'), {
                    'rule': 'most_recent',
                    'selected_source': v.get('source_system', 'unknown'),
                    'rationale': 'Fallback: first non-null value (no timestamps)'
                }

        return None, {'rule': 'most_recent', 'rationale': 'No valid values found'}


class SourcePriorityRule(SurvivorshipRule):
    """Select value based on source priority hierarchy"""

    # Default priority: lower number = higher priority
    DEFAULT_PRIORITY = {
        'crm_primary': 1,
        'crm_secondary': 2,
        'marketing_automation': 3,
    }

    def __init__(self, priority_map: Optional[Dict[str, int]] = None):
        self.priority = priority_map or self.DEFAULT_PRIORITY

    def apply(self, values: List[Dict[str, Any]]) -> Tuple[Any, Dict[str, Any]]:
        if not values:
            return None, {'rule': 'source_priority', 'rationale': 'No values available'}

        # Sort by priority (lower = better)
        sorted_vals = sorted(
            [v for v in values if v.get('value')],
            key=lambda x: self.priority.get(x.get('source_system', ''), 999)
        )

        if sorted_vals:
            winner = sorted_vals[0]
            rejected = [
                {'source': v.get('source_system', 'unknown'),
                 'value': v.get('value'),
                 'priority': self.priority.get(v.get('source_system', ''), 999)}
                for v in sorted_vals[1:]
            ]
            return winner.get('value'), {
                'rule': 'source_priority',
                'selected_source': winner.get('source_system', 'unknown'),
                'source_priority': self.priority.get(winner.get('source_system', ''), 999),
                'rejected_sources': rejected,
                'rationale': f"Selected from highest priority source: {winner.get('source_system', 'unknown')}"
            }

        return None, {'rule': 'source_priority', 'rationale': 'No valid values found'}


class LongestValueRule(SurvivorshipRule):
    """Select the longest (most complete) value"""

    def apply(self, values: List[Dict[str, Any]]) -> Tuple[Any, Dict[str, Any]]:
        if not values:
            return None, {'rule': 'longest_value', 'rationale': 'No values available'}

        valid_values = [v for v in values if v.get('value')]
        if not valid_values:
            return None, {'rule': 'longest_value', 'rationale': 'No valid values found'}

        winner = max(valid_values, key=lambda x: len(str(x.get('value', ''))))
        rejected = [
            {'source': v.get('source_system', 'unknown'),
             'value': v.get('value'),
             'length': len(str(v.get('value', '')))}
            for v in valid_values if v != winner
        ]

        return winner.get('value'), {
            'rule': 'longest_value',
            'selected_source': winner.get('source_system', 'unknown'),
            'selected_length': len(str(winner.get('value', ''))),
            'rejected_sources': rejected,
            'rationale': f"Selected longest/most complete value from {winner.get('source_system', 'unknown')}"
        }


class MinimumValueRule(SurvivorshipRule):
    """Select minimum value (for preserving oldest created_at)"""

    def apply(self, values: List[Dict[str, Any]]) -> Tuple[Any, Dict[str, Any]]:
        if not values:
            return None, {'rule': 'minimum_value', 'rationale': 'No values available'}

        valid_values = [v for v in values if v.get('value')]
        if not valid_values:
            return None, {'rule': 'minimum_value', 'rationale': 'No valid values found'}

        winner = min(valid_values, key=lambda x: str(x.get('value', '')))
        rejected = [
            {'source': v.get('source_system', 'unknown'),
             'value': str(v.get('value', '')),
             'compared_value': str(v.get('value', ''))}
            for v in valid_values if v != winner
        ]

        return winner.get('value'), {
            'rule': 'minimum_value',
            'selected_source': winner.get('source_system', 'unknown'),
            'rejected_sources': rejected,
            'rationale': f"Selected minimum (oldest) value from {winner.get('source_system', 'unknown')}"
        }


class SurvivorshipEngine:
    """
    Attribute-level survivorship policy engine.
    Each attribute has a defined rule with full metadata capture.
    """

    # Attribute -> (Rule, Rationale)
    DEFAULT_POLICIES = {
        'email': (MostRecentRule(), "Recency bias - most recent email is most likely correct"),
        'phone': (SourcePriorityRule(), "Trust hierarchy: CRM Primary > Secondary > Marketing"),
        'company_name': (LongestValueRule(), "Completeness heuristic - longer form has more detail"),
        'first_name': (MostRecentRule(), "Most recent update likely has corrections"),
        'last_name': (SourcePriorityRule(), "CRM sources more reliable for legal names"),
        'title': (MostRecentRule(), "Job titles change over time, use most recent"),
        'created_at': (MinimumValueRule(), "Preserve original relationship timestamp"),
    }

    def __init__(self, policies: Optional[Dict[str, Tuple[SurvivorshipRule, str]]] = None):
        self.policies = policies or self.DEFAULT_POLICIES

    def merge_records(self, records: List[Dict[str, Any]], match_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple source records into a Golden Record.
        Returns: golden_record dict with survivorship decisions.
        """
        if not records:
            return None

        # Extract source record IDs
        source_ids = [r.get('source_record_id', 'unknown') for r in records]
        source_systems = list(set(r.get('source_system', 'unknown') for r in records))

        # Apply survivorship rules per attribute
        golden_attributes = {}
        survivorship_decisions = {}

        for attribute, (rule, rationale) in self.policies.items():
            # Collect all values for this attribute from source records
            values = []
            for record in records:
                raw_value = record.get(attribute)
                # Handle JSON canonical_name
                if attribute == 'first_name' and not raw_value:
                    canonical = record.get('canonical_name')
                    if canonical:
                        try:
                            cn = json.loads(canonical) if isinstance(canonical, str) else canonical
                            raw_value = cn.get('first', '')
                        except:
                            pass
                elif attribute == 'last_name' and not raw_value:
                    canonical = record.get('canonical_name')
                    if canonical:
                        try:
                            cn = json.loads(canonical) if isinstance(canonical, str) else canonical
                            raw_value = cn.get('last', '')
                        except:
                            pass

                if raw_value:
                    values.append({
                        'value': raw_value,
                        'source_system': record.get('source_system', 'unknown'),
                        'source_record_id': record.get('source_record_id', 'unknown'),
                        'updated_at': record.get('updated_at'),
                    })

            # Apply rule
            selected_value, decision = rule.apply(values)
            decision['rationale'] = rationale
            decision['attribute'] = attribute
            golden_attributes[f'canonical_{attribute}' if not attribute.startswith('canonical_') else attribute] = selected_value
            survivorship_decisions[attribute] = decision

        # Build golden record
        golden_record = {
            'source_record_ids': json.dumps(source_ids),
            'canonical_email': golden_attributes.get('canonical_email', ''),
            'canonical_phone': golden_attributes.get('canonical_phone', ''),
            'canonical_first_name': golden_attributes.get('canonical_first_name', ''),
            'canonical_last_name': golden_attributes.get('canonical_last_name', ''),
            'canonical_company': golden_attributes.get('canonical_company_name', ''),
            'canonical_title': golden_attributes.get('canonical_title', ''),
            'canonical_region': records[0].get('normalized_region', records[0].get('region', '')) if records else '',
            'survivorship_metadata': json.dumps(survivorship_decisions),
            'lineage_graph': json.dumps({
                'source_records': source_ids,
                'merge_event': {
                    'type': 'auto_merge' if match_result.get('match_status') == 'auto_merge' else 'reviewed_merge',
                    'confidence': match_result.get('confidence_score'),
                    'timestamp': str(datetime.now()),
                },
                'survivorship_decisions': {k: v for k, v in survivorship_decisions.items()},
            }),
            'version': 1,
            'is_current': True,
        }

        return golden_record

    def get_policies(self) -> Dict[str, str]:
        """Get current policy definitions"""
        return {
            attr: rationale for attr, (rule, rationale) in self.policies.items()
        }

    def update_policy(self, attribute: str, rule: SurvivorshipRule, rationale: str):
        """Update policy for an attribute"""
        self.policies[attribute] = (rule, rationale)
