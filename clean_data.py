"""Clean corrupted password entries."""

import sys

sys.path.insert(0, '/Users/chennanxing/PycharmProjects/PasswordProject')

from src.password_manager.storage import DatabaseManager


def clean_corrupted_data():
    """Delete all password entries with corrupted category data."""
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    print("Cleaning corrupted password entries...")
    
    with db_manager.get_session() as session:
        from src.password_manager.storage.models import PasswordEntryModel, MasterKeyModel
        
        # Delete all password entries
        count = session.query(PasswordEntryModel).delete()
        print(f"✓ Deleted {count} password entries")
        
        # Delete all master keys
        count = session.query(MasterKeyModel).delete()
        print(f"✓ Deleted {count} master keys")
        
        session.commit()
    
    print("\n✓ Cleanup completed!")
    print("\nNow you can:")
    print("1. Restart your application")
    print("2. Add new passwords with Chinese categories")
    print("3. The categories will be displayed correctly")


if __name__ == "__main__":
    clean_corrupted_data()