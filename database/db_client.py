"""
GoldenRecord Database Client
Handles connection to PGlite (or real PostgreSQL) with connection pooling
"""
import os
import sys
import json
import socket
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

# Database configuration
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')


class PGliteJSONAdapter:
    """Adapter to connect to PGlite TCP server using JSON protocol"""

    def __init__(self, host=DB_HOST, port=DB_PORT):
        self.host = host
        self.port = port
        self.conn = None
        self.cur = None
        self._connect()

    def _connect(self):
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=5
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    def execute(self, sql: str, params: tuple = ()):
        self.cur.execute(sql, params)

    def fetchall(self):
        return self.cur.fetchall()

    def fetchone(self):
        return self.cur.fetchone()

    def executemany(self, sql: str, params_list: List[tuple]):
        execute_values(self.cur, sql, params_list)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class Database:
    """Main database interface for GoldenRecord"""

    @staticmethod
    @contextmanager
    def get_connection():
        """Get a database connection context manager"""
        conn = None
        try:
            conn = PGliteJSONAdapter()
            yield conn
        finally:
            if conn:
                conn.close()

    @staticmethod
    def execute(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        with Database.get_connection() as conn:
            conn.execute(sql, params)
            try:
                return conn.fetchall()
            except psycopg2.ProgrammingError:
                return []

    @staticmethod
    def execute_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        with Database.get_connection() as conn:
            conn.execute(sql, params)
            try:
                return conn.fetchone()
            except psycopg2.ProgrammingError:
                return None

    @staticmethod
    def insert_many(table: str, columns: List[str], values: List[tuple]):
        """Bulk insert records"""
        with Database.get_connection() as conn:
            col_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            conn.cur.executemany(sql, values)
            conn.commit()

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        with Database.get_connection() as conn:
            # Raw table counts
            for table in ['raw_crm.primary_leads', 'raw_crm.secondary_leads',
                          'raw_marketing.contacts']:
                conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                result = conn.fetchone()
                stats[table] = result['cnt'] if result else 0

            # Golden records
            conn.execute("SELECT COUNT(*) as cnt FROM marts.golden_records WHERE is_current = TRUE")
            result = conn.fetchone()
            stats['golden_records'] = result['cnt'] if result else 0

            # Match results
            conn.execute("SELECT COUNT(*) as cnt FROM marts.match_results")
            result = conn.fetchone()
            stats['match_results'] = result['cnt'] if result else 0

            # Match status distribution
            conn.execute("""
                SELECT match_status, COUNT(*) as cnt
                FROM marts.match_results
                GROUP BY match_status
            """)
            stats['match_status_dist'] = {r['match_status']: r['cnt'] for r in conn.fetchall()}

        return stats

    @staticmethod
    def reset_database():
        """Reset all data (for demo purposes)"""
        with Database.get_connection() as conn:
            tables = [
                'audit.lineage_events',
                'audit.quality_metrics',
                'audit.reconciliation_log',
                'marts.survivorship_log',
                'marts.golden_records',
                'marts.match_results',
                'intermediate.comparison_features',
                'intermediate.candidate_pairs',
                'intermediate.blocking_index',
                'staging.standardized_records',
                'raw_marketing.contacts',
                'raw_crm.secondary_leads',
                'raw_crm.primary_leads',
            ]
            for table in tables:
                try:
                    conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                except Exception as e:
                    print(f"Warning: Could not truncate {table}: {e}")
            conn.commit()
