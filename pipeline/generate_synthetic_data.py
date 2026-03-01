"""
GoldenRecord Synthetic Data Generator
Generates 120K records across 3 source systems with 15-20% realistic duplicates
"""
import random
import json
import uuid
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_client import Database

# Seed for reproducibility
random.seed(42)

# Sample data pools
FIRST_NAMES = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
    'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
    'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
    'Kenneth', 'Dorothy', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa',
    'Timothy', 'Deborah', 'Ronald', 'Stephanie', 'Edward', 'Rebecca', 'Jason', 'Sharon',
    'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
    'Nicholas', 'Angela', 'Eric', 'Shirley', 'Jonathan', 'Anna', 'Stephen', 'Brenda',
    'Larry', 'Pamela', 'Justin', 'Emma', 'Scott', 'Nicole', 'Brandon', 'Helen',
    'Benjamin', 'Samantha', 'Samuel', 'Katherine', 'Gregory', 'Christine', 'Alexander', 'Debra',
    'Frank', 'Rachel', 'Patrick', 'Catherine', 'Raymond', 'Carolyn', 'Jack', 'Janet',
    'Dennis', 'Ruth', 'Jerry', 'Maria', 'Tyler', 'Heather', 'Aaron', 'Diane'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
    'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young',
    'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
    'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker',
    'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy',
    'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey',
    'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson',
    'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza',
    'Ruiz', 'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers',
    'Long', 'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell'
]

COMPANY_SUFFIXES = ['Inc.', 'LLC', 'Ltd.', 'Corp.', 'Co.', 'Group', 'Partners', 'Associates', '']
COMPANY_PREFIXES = [
    'Tech', 'Global', 'Advanced', 'Digital', 'Smart', 'Innovative', 'Dynamic', 'Strategic',
    'Premier', 'Elite', 'Superior', 'Summit', 'Pinnacle', 'Apex', 'Vanguard', 'Horizon',
    'Nexus', 'Synergy', 'Fusion', 'Quantum', 'Stellar', 'Nova', 'Zenith', 'Catalyst'
]
COMPANY_BASES = [
    'Solutions', 'Systems', 'Services', 'Technologies', 'Software', 'Consulting',
    'Enterprises', 'Industries', 'Holdings', 'Ventures', 'Capital', 'Partners',
    'Analytics', 'Cloud', 'Data', 'Networks', 'Security', 'Robotics', 'AI', 'Digital'
]

REGIONS = ['North America', 'Europe', 'APAC', 'LATAM', 'EMEA', 'South America', 'Asia', 'Middle East']

JOB_TITLES = [
    'CEO', 'CTO', 'CFO', 'COO', 'VP of Sales', 'VP of Marketing', 'VP of Engineering',
    'Director of Sales', 'Director of Marketing', 'Director of IT', 'Sales Manager',
    'Marketing Manager', 'Product Manager', 'Engineering Manager', 'Business Development',
    'Account Executive', 'Sales Representative', 'Marketing Specialist', 'Software Engineer',
    'Data Analyst', 'Product Owner', 'Scrum Master', 'DevOps Engineer', 'Cloud Architect',
    'Data Scientist', 'Machine Learning Engineer', 'Solutions Architect', 'Technical Lead',
    'Project Manager', 'Operations Manager', 'HR Director', 'Finance Manager',
    'Customer Success Manager', 'Support Engineer', 'Security Analyst', 'Network Engineer',
    'Database Administrator', 'System Administrator', 'Quality Assurance Engineer',
    'UX Designer', 'UI Designer', 'Frontend Developer', 'Backend Developer', 'Full Stack Developer'
]

LEAD_SOURCES = ['Website', 'LinkedIn', 'Trade Show', 'Referral', 'Email Campaign',
                'Paid Search', 'Organic Search', 'Social Media', 'Webinar', 'Cold Outreach',
                'Partner', 'Event', 'Content Download', 'Free Trial', 'Demo Request']

EMAIL_DOMAINS = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
    'company.com', 'techcorp.com', 'innovate.io', 'solutions.net',
    'enterprise.org', 'digital.com', 'cloudtech.io', 'datacorp.com',
    'smartbiz.net', 'global.com', 'apex.org', 'nexus.io'
]


class DataGenerator:
    """Generates synthetic CRM and Marketing data with realistic duplicates"""

    def __init__(self, duplicate_rate=0.18):
        self.duplicate_rate = duplicate_rate
        self.generated_emails = set()
        self.duplicate_pool = []  # Records that will be duplicated

    def _random_date(self, start_days_ago=365, end_days_ago=0):
        """Generate a random date within range"""
        days_ago = random.randint(end_days_ago, start_days_ago)
        return datetime.now() - timedelta(days=days_ago)

    def _generate_company_name(self):
        """Generate a realistic company name"""
        prefix = random.choice(COMPANY_PREFIXES)
        base = random.choice(COMPANY_BASES)
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{prefix} {base} {suffix}".strip()

    def _generate_phone(self):
        """Generate a realistic phone number"""
        area = random.randint(200, 999)
        prefix = random.randint(200, 999)
        line = random.randint(1000, 9999)
        return f"+1-{area}-{prefix}-{line}"

    def _generate_email(self, first_name, last_name, company=None):
        """Generate an email address"""
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}",
            f"{last_name.lower()}.{first_name.lower()}",
            f"{first_name.lower()[0]}{last_name.lower()}",
        ]
        base = random.choice(patterns)
        if company:
            domain = f"{company.lower().replace(' ', '').replace('.', '').replace(',', '')}.com"
        else:
            domain = random.choice(EMAIL_DOMAINS)
        return f"{base}@{domain}"

    def _create_duplicate_variation(self, record, variation_type):
        """Create a realistic duplicate with variation"""
        dup = record.copy()
        dup['source_record_id'] = f"SRC-{variation_type.upper()}-{uuid.uuid4().hex[:8]}"
        dup['loaded_at'] = self._random_date(30, 0)  # More recent
        dup['updated_at'] = self._random_date(30, 0)

        if variation_type == 'typo':
            # Typo in email
            email = dup['email']
            if len(email) > 5:
                pos = random.randint(1, len(email) - 3)
                dup['email'] = email[:pos] + random.choice('abcdefghijklmnopqrstuvwxyz') + email[pos+1:]
        elif variation_type == 'nickname':
            # Nickname variation
            nicknames = {'James': 'Jim', 'Robert': 'Bob', 'William': 'Bill', 'Richard': 'Rick',
                        'Michael': 'Mike', 'Thomas': 'Tom', 'Charles': 'Charlie', 'David': 'Dave',
                        'Elizabeth': 'Liz', 'Jennifer': 'Jen', 'Patricia': 'Pat', 'Margaret': 'Maggie'}
            if dup.get('first_name') in nicknames:
                dup['first_name'] = nicknames[dup['first_name']]
        elif variation_type == 'company_suffix':
            # Company name with different suffix
            company = dup.get('company_name', '')
            if company:
                # Remove or change suffix
                for suffix in COMPANY_SUFFIXES:
                    if company.endswith(suffix):
                        company = company[:-len(suffix)].strip()
                        break
                dup['company_name'] = f"{company} {random.choice(COMPANY_SUFFIXES)}"
        elif variation_type == 'phone_format':
            # Different phone format
            phone = dup.get('phone', '')
            if phone:
                digits = ''.join(c for c in phone if c.isdigit())
                if len(digits) == 11:  # +1-xxx-xxx-xxxx
                    dup['phone'] = f"({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        elif variation_type == 'email_alias':
            # + alias in email
            email = dup['email']
            if '@' in email:
                local, domain = email.split('@')
                dup['email'] = f"{local}+{random.choice(['test', 'work', 'personal', '2'])}@{domain}"
        elif variation_type == 'missing_info':
            # Missing some fields
            if random.random() < 0.5:
                dup['phone'] = None
            if random.random() < 0.3:
                dup['title'] = None
        elif variation_type == 'name_reorder':
            # Swap first/last or add middle initial
            if random.random() < 0.5:
                dup['first_name'], dup['last_name'] = dup['last_name'], dup['first_name']
            else:
                dup['first_name'] = f"{dup['first_name']} {random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}."

        return dup

    def _generate_base_record(self, source_system):
        """Generate a single base record"""
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        company = self._generate_company_name()
        email = self._generate_email(first_name, last_name, company)
        phone = self._generate_phone()
        region = random.choice(REGIONS)
        created_at = self._random_date()

        base = {
            'source_record_id': f"SRC-{source_system.upper()}-{uuid.uuid4().hex[:8]}",
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'company_name': company,
            'region': region,
            'created_at': created_at,
            'updated_at': created_at + timedelta(days=random.randint(1, 30)),
            'loaded_at': datetime.now(),
        }
        return base

    def generate_crm_primary(self, count=80000):
        """Generate CRM Primary leads (~80K)"""
        print(f"Generating {count} CRM Primary leads...")
        records = []
        duplicate_count = int(count * self.duplicate_rate)
        base_count = count - duplicate_count

        # Generate base records
        for i in range(base_count):
            record = self._generate_base_record('crm_primary')
            record['lead_source'] = random.choice(LEAD_SOURCES)
            record['title'] = random.choice(JOB_TITLES)
            record['source_system'] = 'crm_primary'
            record['raw_data'] = json.dumps(record, default=str)
            records.append(record)

            # Store some for duplication
            if i < duplicate_count:
                self.duplicate_pool.append(record.copy())

            if (i + 1) % 10000 == 0:
                print(f"  CRM Primary: {i + 1} base records generated")

        # Generate duplicates with variations
        print(f"  Generating {duplicate_count} duplicates with variations...")
        variation_types = ['typo', 'nickname', 'company_suffix', 'phone_format',
                          'email_alias', 'missing_info', 'name_reorder']

        for i in range(duplicate_count):
            if i < len(self.duplicate_pool):
                original = self.duplicate_pool[i]
                variation = random.choice(variation_types)
                dup = self._create_duplicate_variation(original, variation)
                dup['lead_source'] = random.choice(LEAD_SOURCES)
                dup['title'] = random.choice(JOB_TITLES)
                dup['source_system'] = 'crm_primary'
                dup['raw_data'] = json.dumps(dup, default=str)
                records.append(dup)

            if (i + 1) % 5000 == 0:
                print(f"  CRM Primary: {i + 1} duplicates generated")

        print(f"  CRM Primary: {len(records)} total records")
        return records

    def generate_crm_secondary(self, count=25000):
        """Generate CRM Secondary leads (~25K)"""
        print(f"Generating {count} CRM Secondary leads...")
        records = []
        duplicate_count = int(count * self.duplicate_rate)
        base_count = count - duplicate_count

        for i in range(base_count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            company = self._generate_company_name()
            email = self._generate_email(first_name, last_name)

            # Some overlap with primary records (cross-system duplicates)
            if random.random() < 0.3 and self.duplicate_pool:
                original = random.choice(self.duplicate_pool)
                first_name = original['first_name']
                last_name = original['last_name']
                email = original['email']
                company = original['company_name']

            record = {
                'source_record_id': f"SRC-CRM-SEC-{uuid.uuid4().hex[:8]}",
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'mobile': self._generate_phone(),
                'org_name': company,
                'region': random.choice(REGIONS),
                'job_title': random.choice(JOB_TITLES),
                'source_system': 'crm_secondary',
                'created_at': self._random_date(),
                'updated_at': self._random_date(),
                'loaded_at': datetime.now(),
                'raw_data': json.dumps({'first_name': first_name, 'last_name': last_name,
                                       'email': email, 'mobile': self._generate_phone(),
                                       'org_name': company, 'region': random.choice(REGIONS)}, default=str)
            }
            records.append(record)

            if (i + 1) % 5000 == 0:
                print(f"  CRM Secondary: {i + 1} records generated")

        # Add cross-system duplicates
        for i in range(duplicate_count):
            if self.duplicate_pool and i < len(self.duplicate_pool):
                original = self.duplicate_pool[i]
                record = {
                    'source_record_id': f"SRC-CRM-SEC-{uuid.uuid4().hex[:8]}",
                    'first_name': original['first_name'],
                    'last_name': original['last_name'],
                    'email': original['email'],
                    'mobile': original.get('phone', self._generate_phone()),
                    'org_name': original.get('company_name', self._generate_company_name()),
                    'region': original.get('region', random.choice(REGIONS)),
                    'job_title': random.choice(JOB_TITLES),
                    'source_system': 'crm_secondary',
                    'created_at': self._random_date(),
                    'updated_at': self._random_date(),
                    'loaded_at': datetime.now(),
                    'raw_data': json.dumps(original, default=str)
                }
                records.append(record)

        print(f"  CRM Secondary: {len(records)} total records")
        return records

    def generate_marketing(self, count=15000):
        """Generate Marketing Automation contacts (~15K)"""
        print(f"Generating {count} Marketing contacts...")
        records = []
        duplicate_count = int(count * self.duplicate_rate)
        base_count = count - duplicate_count

        for i in range(base_count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = self._generate_email(first_name, last_name)
            domain = email.split('@')[1]

            record = {
                'source_record_id': f"SRC-MKT-{uuid.uuid4().hex[:8]}",
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'domain': domain,
                'job_title': random.choice(JOB_TITLES),
                'company_name': self._generate_company_name(),
                'region': random.choice(REGIONS),
                'source_system': 'marketing_automation',
                'created_at': self._random_date(),
                'updated_at': self._random_date(),
                'loaded_at': datetime.now(),
                'raw_data': json.dumps({'first_name': first_name, 'last_name': last_name,
                                       'email': email, 'domain': domain}, default=str)
            }
            records.append(record)

        # Cross-system duplicates from CRM
        for i in range(duplicate_count):
            if self.duplicate_pool and i < len(self.duplicate_pool):
                original = self.duplicate_pool[i + 1000]  # Different subset
                email = original['email']
                domain = email.split('@')[1] if '@' in email else 'unknown.com'

                record = {
                    'source_record_id': f"SRC-MKT-{uuid.uuid4().hex[:8]}",
                    'first_name': original['first_name'],
                    'last_name': original['last_name'],
                    'email': email,
                    'domain': domain,
                    'job_title': random.choice(JOB_TITLES),
                    'company_name': original.get('company_name', self._generate_company_name()),
                    'region': original.get('region', random.choice(REGIONS)),
                    'source_system': 'marketing_automation',
                    'created_at': self._random_date(),
                    'updated_at': self._random_date(),
                    'loaded_at': datetime.now(),
                    'raw_data': json.dumps(original, default=str)
                }
                records.append(record)

        print(f"  Marketing: {len(records)} total records")
        return records

    def load_to_database(self, records, table):
        """Load records into database"""
        print(f"Loading {len(records)} records into {table}...")

        with Database.get_connection() as conn:
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                if table == 'raw_crm.primary_leads':
                    values = [
                        (r['source_record_id'], r['source_system'], r['loaded_at'],
                         r['email'], r['phone'], r['company_name'], r.get('lead_source'),
                         r['first_name'], r['last_name'], r.get('title'), r['region'],
                         r['created_at'], r['updated_at'], r['raw_data'])
                        for r in batch
                    ]
                    sql = """
                        INSERT INTO raw_crm.primary_leads
                        (source_record_id, source_system, loaded_at, email, phone,
                         company_name, lead_source, first_name, last_name, title, region,
                         created_at, updated_at, raw_data)
                        VALUES %s ON CONFLICT DO NOTHING
                    """
                    execute_values(conn.cur, sql, values)

                elif table == 'raw_crm.secondary_leads':
                    values = [
                        (r['source_record_id'], r['source_system'], r['loaded_at'],
                         r['email'], r['mobile'], r['org_name'], r['region'],
                         r['first_name'], r['last_name'], r['job_title'],
                         r['created_at'], r['updated_at'], r['raw_data'])
                        for r in batch
                    ]
                    sql = """
                        INSERT INTO raw_crm.secondary_leads
                        (source_record_id, source_system, loaded_at, email, mobile,
                         org_name, region, first_name, last_name, job_title,
                         created_at, updated_at, raw_data)
                        VALUES %s ON CONFLICT DO NOTHING
                    """
                    execute_values(conn.cur, sql, values)

                elif table == 'raw_marketing.contacts':
                    values = [
                        (r['source_record_id'], r['source_system'], r['loaded_at'],
                         r['email'], r['domain'], r['job_title'],
                         r['first_name'], r['last_name'], r['company_name'], r['region'],
                         r['created_at'], r['updated_at'], r['raw_data'])
                        for r in batch
                    ]
                    sql = """
                        INSERT INTO raw_marketing.contacts
                        (source_record_id, source_system, loaded_at, email, domain,
                         job_title, first_name, last_name, company_name, region,
                         created_at, updated_at, raw_data)
                        VALUES %s ON CONFLICT DO NOTHING
                    """
                    execute_values(conn.cur, sql, values)

                conn.commit()
                if (i + batch_size) % 10000 == 0 or i == 0:
                    print(f"  Loaded {min(i + batch_size, len(records))} / {len(records)}")

        print(f"  Done loading {table}")


def main():
    """Main entry point for data generation"""
    print("=" * 60)
    print("GoldenRecord: Synthetic Data Generation")
    print("=" * 60)

    # Start the PGlite server first (this would be started separately)
    # For now, we assume it's running

    # Check connection
    try:
        result = Database.execute("SELECT 1 as test")
        print(f"Database connection OK: {result}")
    except Exception as e:
        print(f"WARNING: Could not connect to database: {e}")
        print("Please start the PGlite server first: node database/pglite-server.mjs")
        sys.exit(1)

    # Reset database
    print("\nResetting database...")
    Database.reset_database()

    # Generate data
    generator = DataGenerator(duplicate_rate=0.18)

    # CRM Primary: ~80K
    crm_primary = generator.generate_crm_primary(count=80000)
    generator.load_to_database(crm_primary, 'raw_crm.primary_leads')

    # CRM Secondary: ~25K
    crm_secondary = generator.generate_crm_secondary(count=25000)
    generator.load_to_database(crm_secondary, 'raw_crm.secondary_leads')

    # Marketing: ~15K
    marketing = generator.generate_marketing(count=15000)
    generator.load_to_database(marketing, 'raw_marketing.contacts')

    # Print summary
    print("\n" + "=" * 60)
    print("Data Generation Complete!")
    print("=" * 60)
    stats = Database.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value:,}")

    total = sum(v for k, v in stats.items() if k.startswith('raw_'))
    print(f"\n  Total raw records: {total:,}")


if __name__ == '__main__':
    main()
