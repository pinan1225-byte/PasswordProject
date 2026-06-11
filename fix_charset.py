"""Fix database charset for Chinese character support."""

import sys
from sqlalchemy import create_engine, text

sys.path.insert(0, '/Users/chennanxing/PycharmProjects/PasswordProject')

from src.password_manager.config import get_settings


def fix_database_charset():
    """Fix database and tables charset to utf8mb4."""
    settings = get_settings()
    
    # Connect without specifying database
    base_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
    )
    
    engine = create_engine(base_url)
    
    with engine.connect() as conn:
        # Alter database charset
        print("Fixing database charset...")
        conn.execute(text(f"ALTER DATABASE {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()
        print("✓ Database charset fixed")
    
    # Connect to the specific database
    db_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    )
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get all tables
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        
        print(f"\nFound {len(tables)} tables: {', '.join(tables)}")
        
        # Fix each table
        for table in tables:
            print(f"\nFixing table: {table}")
            conn.execute(text(f"ALTER TABLE {table} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"✓ Table {table} charset fixed")
        
        # Fix specific columns in password_entries table
        print("\n\nFixing specific columns in password_entries...")
        
        columns_to_fix = [
            ("title", "VARCHAR(255)"),
            ("username", "VARCHAR(255)"),
            ("url", "VARCHAR(2048)"),
            ("notes", "TEXT"),
            ("category", "VARCHAR(100)"),
        ]
        
        for column, col_type in columns_to_fix:
            try:
                print(f"  Fixing column: {column}")
                conn.execute(text(f"""
                    ALTER TABLE password_entries 
                    MODIFY COLUMN {column} {col_type} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """))
                conn.commit()
                print(f"  ✓ Column {column} fixed")
            except Exception as e:
                print(f"  ✗ Error fixing column {column}: {e}")
        
        # Fix users table
        print("\n\nFixing users table columns...")
        users_columns = [
            ("username", "VARCHAR(255)"),
            ("email", "VARCHAR(255)"),
        ]
        
        for column, col_type in users_columns:
            try:
                print(f"  Fixing column: {column}")
                conn.execute(text(f"""
                    ALTER TABLE users 
                    MODIFY COLUMN {column} {col_type} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """))
                conn.commit()
                print(f"  ✓ Column {column} fixed")
            except Exception as e:
                print(f"  ✗ Error fixing column {column}: {e}")
    
    print("\n\n✓ All charset fixes completed!")
    print("\nNow you need to:")
    print("1. Delete existing password entries (they have corrupted data)")
    print("2. Restart your application")
    print("3. Add new passwords with Chinese categories")


if __name__ == "__main__":
    fix_database_charset()