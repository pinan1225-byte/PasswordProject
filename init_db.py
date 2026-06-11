#!/usr/bin/env python3
"""Database initialization script."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from src.password_manager.config import get_settings
from src.password_manager.storage.models import Base


def init_database():
    """Initialize database and create tables."""
    settings = get_settings()
    
    # Connect to MySQL server (without database)
    server_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
    )
    
    print(f"🔗 Connecting to MySQL server at {settings.MYSQL_HOST}:{settings.MYSQL_PORT}...")

    try:
        # Validate database name to prevent SQL injection
        import re
        db_name = settings.MYSQL_DATABASE
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            raise ValueError(f"Invalid database name: '{db_name}'. Only alphanumeric and underscore allowed.")

        # Create engine without database
        engine = create_engine(server_url, echo=False)

        # Create database if not exists
        with engine.connect() as conn:
            print(f"📦 Creating database '{db_name}' if not exists...")
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
            conn.commit()
            print(f"✅ Database '{db_name}' is ready!")
        
        engine.dispose()
        
        # Connect to the specific database
        print(f"🔗 Connecting to database '{settings.MYSQL_DATABASE}'...")
        db_engine = create_engine(settings.database_url, echo=False)
        
        # Create all tables
        print("📋 Creating tables...")
        Base.metadata.create_all(db_engine)
        
        # Verify tables
        with db_engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"✅ Created tables: {', '.join(tables)}")
        
        db_engine.dispose()
        
        print("\n🎉 Database initialization completed successfully!")
        print("\n📊 Database Info:")
        print(f"  Host: {settings.MYSQL_HOST}")
        print(f"  Port: {settings.MYSQL_PORT}")
        print(f"  Database: {settings.MYSQL_DATABASE}")
        print(f"  User: {settings.MYSQL_USER}")
        print("\n✨ You can now start the application!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {str(e)}")
        print("\n💡 Please check:")
        print("  1. MySQL server is running")
        print("  2. Connection settings in .env file are correct")
        print("  3. User has permission to create databases")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)