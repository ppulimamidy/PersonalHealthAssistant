#!/usr/bin/env python3
"""
Check PostgreSQL Extensions for Personal Health Assistant
This script verifies which extensions are available and installed.
"""

import psycopg2
import os
import sys
from typing import List, Dict, Tuple

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="54323",
            database="postgres",
            user="postgres",
            password="your-super-secret-and-long-postgres-password"
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def get_available_extensions(conn) -> List[str]:
    """Get list of available extensions"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, default_version, installed_version 
                FROM pg_available_extensions 
                ORDER BY name
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Failed to get available extensions: {e}")
        return []

def get_installed_extensions(conn) -> List[str]:
    """Get list of installed extensions"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT extname, extversion 
                FROM pg_extension 
                ORDER BY extname
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Failed to get installed extensions: {e}")
        return []

def install_extension(conn, extension_name: str) -> bool:
    """Install a PostgreSQL extension"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE EXTENSION IF NOT EXISTS {extension_name}")
            conn.commit()
            print(f"✅ Installed extension: {extension_name}")
            return True
    except Exception as e:
        print(f"❌ Failed to install {extension_name}: {e}")
        return False

def check_critical_extensions() -> List[str]:
    """List of critical extensions for the Personal Health Assistant"""
    return [
        "pgcrypto",           # Cryptographic functions
        "vector",             # Vector embeddings (if available)
        "pg_trgm",            # Fuzzy text matching
        "fuzzystrmatch",      # String similarity
        "jsquery",            # Advanced JSON querying
        "timescaledb",        # Time-series optimization
        "pg_stat_statements", # Query monitoring
        "unaccent",           # Text search without accents
        "tablefunc",          # Crosstab functions
        "postgis",            # Geographic data (if needed)
        "citext",             # Case-insensitive text
        "hstore",             # Key-value store
        "http",               # HTTP client
        "pg_notify",          # Notifications
    ]

def main():
    print("🔍 Checking PostgreSQL Extensions for Personal Health Assistant")
    print("=" * 60)
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Get available and installed extensions
        available = get_available_extensions(conn)
        installed = get_installed_extensions(conn)
        
        print(f"\n📊 Found {len(available)} available extensions")
        print(f"📦 Found {len(installed)} installed extensions")
        
        # Create lookup dictionaries
        available_dict = {row[0]: row for row in available}
        installed_dict = {row[0]: row for row in installed}
        
        # Check critical extensions
        critical_extensions = check_critical_extensions()
        
        print(f"\n🎯 Critical Extensions Status:")
        print("-" * 40)
        
        all_good = True
        for ext in critical_extensions:
            if ext in installed_dict:
                print(f"✅ {ext:<20} - Installed (v{installed_dict[ext][1]})")
            elif ext in available_dict:
                print(f"⚠️  {ext:<20} - Available but not installed")
                all_good = False
            else:
                print(f"❌ {ext:<20} - Not available")
                all_good = False
        
        # Show all available extensions
        print(f"\n📋 All Available Extensions:")
        print("-" * 40)
        for name, default_ver, installed_ver in available:
            status = "✅ Installed" if installed_ver else "⏳ Available"
            print(f"{name:<25} - {status}")
        
        # Offer to install missing critical extensions
        missing_critical = [ext for ext in critical_extensions 
                          if ext in available_dict and ext not in installed_dict]
        
        if missing_critical:
            print(f"\n🔧 Missing Critical Extensions:")
            print("-" * 40)
            for ext in missing_critical:
                print(f"  • {ext}")
            
            response = input(f"\n🤔 Install missing critical extensions? (y/N): ")
            if response.lower() in ['y', 'yes']:
                print("\n🔧 Installing missing extensions...")
                for ext in missing_critical:
                    install_extension(conn, ext)
                print("✅ Installation complete!")
            else:
                print("⏭️  Skipping extension installation")
        
        if all_good:
            print(f"\n🎉 All critical extensions are ready!")
        else:
            print(f"\n⚠️  Some critical extensions are missing or not installed")
        
        # Show extension recommendations
        print(f"\n💡 Extension Recommendations for Personal Health Assistant:")
        print("-" * 60)
        recommendations = {
            "vector": "Essential for AI embeddings and similarity search",
            "timescaledb": "Optimizes time-series health data queries",
            "pg_trgm": "Enables fuzzy matching for medical terms",
            "jsquery": "Advanced JSON querying for flexible data",
            "postgis": "For location-based health analytics",
            "madlib": "Machine learning algorithms for health insights",
            "pgaudit": "Comprehensive audit logging for compliance",
            "pg_stat_statements": "Query performance monitoring"
        }
        
        for ext, description in recommendations.items():
            status = "✅" if ext in installed_dict else "❌"
            print(f"{status} {ext:<20} - {description}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main() 