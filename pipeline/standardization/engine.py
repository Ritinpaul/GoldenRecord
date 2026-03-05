"""
GoldenRecord Canonicalization Engine
Standardizes names, emails, phones, and company names for matching
"""
import re
import json
from typing import Dict, Any, Optional, Tuple
from fuzzywuzzy import fuzz
import Levenshtein


class NameParser:
    """Parse full names into components"""

    PREFIXES = {'dr', 'mr', 'mrs', 'ms', 'miss', 'prof', 'sir', 'lady', 'lord',
                'capt', 'major', 'col', 'gen', 'rev', 'hon'}
    SUFFIXES = {'jr', 'sr', 'ii', 'iii', 'iv', 'v', 'md', 'phd', 'jd', 'dds',
                'esq', 'cpa', 'mba'}

    @staticmethod
    def parse(full_name: str) -> Dict[str, str]:
        """Parse a full name into structured components"""
        if not full_name:
            return {'prefix': '', 'first': '', 'middle': '', 'last': '', 'suffix': ''}

        parts = full_name.lower().strip().split()
        if not parts:
            return {'prefix': '', 'first': '', 'middle': '', 'last': '', 'suffix': ''}

        result = {'prefix': '', 'first': '', 'middle': '', 'last': '', 'suffix': ''}

        # Extract prefix
        if parts[0].rstrip('.') in NameParser.PREFIXES:
            result['prefix'] = parts[0].rstrip('.')
            parts = parts[1:]

        # Extract suffix
        if parts and parts[-1].rstrip('.') in NameParser.SUFFIXES:
            result['suffix'] = parts[-1].rstrip('.')
            parts = parts[:-1]

        # Remaining parts: first, optional middle, last
        if len(parts) == 1:
            result['first'] = parts[0]
        elif len(parts) == 2:
            result['first'] = parts[0]
            result['last'] = parts[1]
        elif len(parts) >= 3:
            result['first'] = parts[0]
            result['last'] = parts[-1]
            result['middle'] = ' '.join(parts[1:-1])

        return result

    @staticmethod
    def canonicalize(full_name: str) -> str:
        """Return canonical form of name (lowercase, cleaned)"""
        parsed = NameParser.parse(full_name)
        parts = [parsed['first']]
        if parsed['middle']:
            parts.append(parsed['middle'])
        if parsed['last']:
            parts.append(parsed['last'])
        return ' '.join(parts)


class EmailNormalizer:
    """Normalize email addresses for matching"""

    @staticmethod
    def normalize(email: str) -> str:
        """Normalize email: lowercase, remove +aliases"""
        if not email:
            return ''

        email = email.lower().strip()

        # Remove + aliases (e.g., john+test@gmail.com -> john@gmail.com)
        if '+' in email:
            local, domain = email.split('@', 1)
            local = local.split('+')[0]
            email = f"{local}@{domain}"

        # Remove dots from Gmail addresses
        if '@gmail.com' in email:
            local, domain = email.split('@', 1)
            local = local.replace('.', '')
            email = f"{local}@{domain}"

        return email

    @staticmethod
    def get_domain(email: str) -> str:
        """Extract domain from email"""
        if not email or '@' not in email:
            return ''
        return email.split('@')[1]


class PhoneStandardizer:
    """Standardize phone numbers to E.164 format"""

    @staticmethod
    def standardize(phone: str) -> str:
        """Standardize phone to E.164-like format"""
        if not phone:
            return ''

        # Extract digits
        digits = re.sub(r'\D', '', phone)

        # If starts with 1 and has 11 digits, it's US
        if len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"

        # If 10 digits, assume US
        if len(digits) == 10:
            return f"+1{digits}"

        # Otherwise return as-is with + prefix
        if len(digits) > 0:
            return f"+{digits}"

        return ''

    @staticmethod
    def get_last_n_digits(phone: str, n: int = 3) -> str:
        """Get last N digits for blocking"""
        digits = re.sub(r'\D', '', phone)
        return digits[-n:] if len(digits) >= n else digits


class CompanyNormalizer:
    """Normalize company names for fuzzy matching"""

    SUFFIXES = {'inc', 'inc.', 'llc', 'llc.', 'ltd', 'ltd.', 'corp', 'corp.',
                'co', 'co.', 'company', 'group', 'holdings', 'partners',
                'associates', 'enterprise', 'enterprises'}

    STOP_WORDS = {'the', 'of', 'and', '&', 'a', 'an'}

    @staticmethod
    def normalize(company: str) -> str:
        """Remove legal suffixes and normalize"""
        if not company:
            return ''

        # Lowercase
        company = company.lower().strip()

        # Remove common suffixes
        parts = company.split()
        cleaned = []
        for part in parts:
            if part.rstrip('.') not in CompanyNormalizer.SUFFIXES:
                cleaned.append(part)

        if not cleaned:
            return company  # Return original if everything was suffixes

        return ' '.join(cleaned)

    @staticmethod
    def get_tokens(company: str) -> set:
        """Get token set for Jaccard similarity"""
        normalized = CompanyNormalizer.normalize(company)
        tokens = set()
        for word in normalized.split():
            word = word.strip()
            if word and word not in CompanyNormalizer.STOP_WORDS:
                tokens.add(word)
        return tokens

    @staticmethod
    def token_jaccard(company_a: str, company_b: str) -> float:
        """Calculate token Jaccard similarity"""
        tokens_a = CompanyNormalizer.get_tokens(company_a)
        tokens_b = CompanyNormalizer.get_tokens(company_b)

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b

        if not union:
            return 0.0

        return len(intersection) / len(union)


class StandardizationEngine:
    """Main standardization engine that processes raw records"""

    def __init__(self):
        self.name_parser = NameParser()
        self.email_normalizer = EmailNormalizer()
        self.phone_standardizer = PhoneStandardizer()
        self.company_normalizer = CompanyNormalizer()

    def standardize_record(self, record: Dict[str, Any], source_system: str) -> Dict[str, Any]:
        """Standardize a single raw record"""
        result = {
            'source_record_id': record.get('source_record_id', ''),
            'source_system': source_system,
            'first_name': '',
            'last_name': '',
            'title': '',
            'company_name': '',
            'email': '',
            'phone': '',
            'region': '',
            'lead_source': '',
            'created_at': record.get('created_at'),
            'updated_at': record.get('updated_at'),
        }

        # Extract fields based on source system
        if source_system == 'crm_primary':
            result['first_name'] = record.get('first_name', '') or ''
            result['last_name'] = record.get('last_name', '') or ''
            result['title'] = record.get('title', '') or ''
            result['company_name'] = record.get('company_name', '') or ''
            result['email'] = record.get('email', '') or ''
            result['phone'] = record.get('phone', '') or ''
            result['region'] = record.get('region', '') or ''
            result['lead_source'] = record.get('lead_source', '') or ''

        elif source_system == 'crm_secondary':
            result['first_name'] = record.get('first_name', '') or ''
            result['last_name'] = record.get('last_name', '') or ''
            result['title'] = record.get('job_title', '') or ''
            result['company_name'] = record.get('org_name', '') or ''
            result['email'] = record.get('email', '') or ''
            result['phone'] = record.get('mobile', '') or ''
            result['region'] = record.get('region', '') or ''

        elif source_system == 'marketing_automation':
            result['first_name'] = record.get('first_name', '') or ''
            result['last_name'] = record.get('last_name', '') or ''
            result['title'] = record.get('job_title', '') or ''
            result['company_name'] = record.get('company_name', '') or ''
            result['email'] = record.get('email', '') or ''
            result['phone'] = ''  # Marketing has no phone
            result['region'] = record.get('region', '') or ''

        # Apply standardization
        # Parse name
        full_name = f"{result['first_name']} {result['last_name']}".strip()
        parsed_name = self.name_parser.parse(full_name)

        # Normalize email
        canonical_email = self.email_normalizer.normalize(result['email'])
        email_domain = self.email_normalizer.get_domain(result['email'])

        # Standardize phone
        canonical_phone = self.phone_standardizer.standardize(result['phone'])

        # Normalize company
        canonical_company = self.company_normalizer.normalize(result['company_name'])

        # Build standardization metadata
        metadata = {
            'original_name': full_name,
            'parsed_name': parsed_name,
            'email_normalized': canonical_email != result['email'].lower(),
            'phone_standardized': canonical_phone != result['phone'],
            'company_suffix_removed': canonical_company != result['company_name'].lower(),
            'normalization_timestamp': str(record.get('loaded_at')),
        }

        result['canonical_email'] = canonical_email
        result['canonical_phone'] = canonical_phone
        result['canonical_name'] = json.dumps(parsed_name)
        result['canonical_company'] = canonical_company
        result['normalized_region'] = (result['region'] or '').lower().strip()
        result['standardization_metadata'] = json.dumps(metadata)

        return result

    def standardize_batch(self, records: list, source_system: str) -> list:
        """Standardize a batch of records"""
        return [self.standardize_record(r, source_system) for r in records]
