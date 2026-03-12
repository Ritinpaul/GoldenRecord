"""
GoldenRecord Confidence Scoring Engine
Two-tier approach:
  Tier A: Weighted sum (fast path)
  Tier B: ML classifier (slow path for ambiguous 0.60-0.85 band)
"""
import json
import math
from typing import Dict, Any, List, Optional, Tuple
from fuzzywuzzy import fuzz
import Levenshtein

from pipeline.standardization.engine import (
    NameParser, EmailNormalizer, PhoneStandardizer, CompanyNormalizer
)


class ComparisonFeatures:
    """Generate comparison features for a pair of records"""

    def __init__(self):
        self.name_parser = NameParser()
        self.email_normalizer = EmailNormalizer()
        self.company_normalizer = CompanyNormalizer()

    def compute(self, record_a: Dict, record_b: Dict) -> Dict[str, float]:
        """Compute all comparison features for a pair"""
        features = {}

        # Email features
        email_a = (record_a.get('canonical_email', '') or record_a.get('email', '')).lower().strip()
        email_b = (record_b.get('canonical_email', '') or record_b.get('email', '')).lower().strip()

        features['email_exact'] = 1.0 if email_a and email_b and email_a == email_b else 0.0

        # Email domain
        domain_a = email_a.split('@')[1] if '@' in email_a else ''
        domain_b = email_b.split('@')[1] if '@' in email_b else ''
        features['email_domain'] = 1.0 if domain_a and domain_b and domain_a == domain_b else 0.0

        # Name similarity (Jaro-Winkler)
        name_a = f"{record_a.get('first_name', '')} {record_a.get('last_name', '')}".strip().lower()
        name_b = f"{record_b.get('first_name', '')} {record_b.get('last_name', '')}".strip().lower()

        if name_a and name_b:
            # Use Jaro-Winkler for name similarity
            features['name_jaro_winkler'] = Levenshtein.jaro_winkler(name_a, name_b)
        else:
            features['name_jaro_winkler'] = 0.0

        # Phone exact match
        phone_a = (record_a.get('canonical_phone', '') or record_a.get('phone', '')).strip()
        phone_b = (record_b.get('canonical_phone', '') or record_b.get('phone', '')).strip()

        # Normalize phones for comparison
        phone_a_digits = ''.join(c for c in phone_a if c.isdigit())
        phone_b_digits = ''.join(c for c in phone_b if c.isdigit())

        features['phone_exact'] = 1.0 if phone_a_digits and phone_b_digits and phone_a_digits == phone_b_digits else 0.0

        # Company token Jaccard
        company_a = (record_a.get('canonical_company', '') or record_a.get('company_name', '')).lower().strip()
        company_b = (record_b.get('canonical_company', '') or record_b.get('company_name', '')).lower().strip()

        features['company_token_jaccard'] = self.company_normalizer.token_jaccard(company_a, company_b)

        return features


class ConfidenceScorer:
    """
    Tier A: Weighted sum confidence scoring
    Tier B: ML classifier placeholder (see TODO.md)
    """

    # Feature weights (sum to 1.0)
    FEATURE_WEIGHTS = {
        'email_exact': 0.35,
        'email_domain': 0.10,
        'name_jaro_winkler': 0.20,
        'phone_exact': 0.25,
        'company_token_jaccard': 0.10,
    }

    # Decision thresholds
    AUTO_MERGE_THRESHOLD = 0.85
    REVIEW_THRESHOLD = 0.60

    def __init__(self):
        self.comparator = ComparisonFeatures()

    def compute_confidence(self, features: Dict[str, float]) -> float:
        """Tier A: Weighted sum confidence"""
        confidence = 0.0
        for feature_name, weight in self.FEATURE_WEIGHTS.items():
            value = features.get(feature_name, 0.0)
            confidence += value * weight
        return min(1.0, max(0.0, confidence))

    def classify(self, confidence: float) -> str:
        """Classify match status based on confidence"""
        if confidence >= self.AUTO_MERGE_THRESHOLD:
            return 'auto_merge'
        elif confidence >= self.REVIEW_THRESHOLD:
            return 'review'
        else:
            return 'distinct'

    def score_pair(self, record_a: Dict, record_b: Dict) -> Dict[str, Any]:
        """Score a candidate pair and return full result"""
        # Compute features
        features = self.comparator.compute(record_a, record_b)

        # Tier A: Weighted sum
        confidence = self.compute_confidence(features)
        tier = 'tier_a'

        # Tier B placeholder: ML classifier for ambiguous band
        if self.REVIEW_THRESHOLD <= confidence < self.AUTO_MERGE_THRESHOLD:
            tier = 'tier_b_pending'
            # ML would refine confidence here - see TODO.md
            # For now, keep Tier A score with a flag

        status = self.classify(confidence)

        return {
            'record_a_id': record_a.get('id'),
            'record_b_id': record_b.get('id'),
            'email_exact': features['email_exact'],
            'email_domain': features['email_domain'],
            'name_jaro_winkler': round(features['name_jaro_winkler'], 6),
            'phone_exact': features['phone_exact'],
            'company_token_jaccard': round(features['company_token_jaccard'], 6),
            'confidence_score': round(confidence, 6),
            'match_status': status,
            'match_tier': tier,
        }

    def score_batch(self, pairs: List[Dict], records: Dict[int, Dict]) -> List[Dict]:
        """Score a batch of candidate pairs"""
        results = []
        total = len(pairs)

        for i, pair in enumerate(pairs):
            record_a = records.get(pair['record_a_id'])
            record_b = records.get(pair['record_b_id'])

            if not record_a or not record_b:
                continue

            result = self.score_pair(record_a, record_b)
            result['block_type'] = pair.get('block_type', 'unknown')
            results.append(result)

            if (i + 1) % 10000 == 0:
                print(f"  Scored {i + 1:,} / {total:,} pairs")

        return results

    def get_feature_weights(self) -> Dict[str, float]:
        """Return current feature weights"""
        return self.FEATURE_WEIGHTS.copy()

    def get_thresholds(self) -> Dict[str, float]:
        """Return decision thresholds"""
        return {
            'auto_merge': self.AUTO_MERGE_THRESHOLD,
            'review': self.REVIEW_THRESHOLD,
        }

    def explain_decision(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate human-readable explanation of a match decision"""
        features = {
            'email_exact': result.get('email_exact', 0),
            'email_domain': result.get('email_domain', 0),
            'name_jaro_winkler': result.get('name_jaro_winkler', 0),
            'phone_exact': result.get('phone_exact', 0),
            'company_token_jaccard': result.get('company_token_jaccard', 0),
        }

        contributing_factors = []
        for feature, value in features.items():
            if value > 0:
                weight = self.FEATURE_WEIGHTS.get(feature, 0)
                contribution = value * weight
                contributing_factors.append({
                    'feature': feature,
                    'value': round(value, 4),
                    'weight': weight,
                    'contribution': round(contribution, 4),
                })

        contributing_factors.sort(key=lambda x: x['contribution'], reverse=True)

        return {
            'confidence': result.get('confidence_score'),
            'status': result.get('match_status'),
            'tier': result.get('match_tier'),
            'top_factors': contributing_factors[:3],
            'threshold_explanation': self._explain_threshold(result.get('confidence_score', 0)),
        }

    def _explain_threshold(self, confidence: float) -> str:
        """Explain why a record was classified a certain way"""
        if confidence >= self.AUTO_MERGE_THRESHOLD:
            return f"Confidence ({confidence:.3f}) >= auto-merge threshold ({self.AUTO_MERGE_THRESHOLD})"
        elif confidence >= self.REVIEW_THRESHOLD:
            return f"Confidence ({confidence:.3f}) in review queue range [{self.REVIEW_THRESHOLD}, {self.AUTO_MERGE_THRESHOLD})"
        else:
            return f"Confidence ({confidence:.3f}) below review threshold ({self.REVIEW_THRESHOLD})"
