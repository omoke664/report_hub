# db.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# -------------------------
# Database Configuration
# -------------------------
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///report_manager.db')
engine = create_engine(DB_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------
# Initialize Database
# -------------------------
def init_db(Base, Role):
    """
    Create tables and default roles if they do not exist.
    Base and Role must be passed to avoid circular imports.
    """
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Migration for existing users table
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            if "reset_token" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN reset_token TEXT"))
                print("[DB] Added reset_token column to users table.")
            if "reset_token_expiry" not in columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME"))
                print("[DB] Added reset_token_expiry column to users table.")
            connection.commit()

    except Exception as e:
        print(f"[DB][Error] Failed to create tables or migrate schema: {e}")
        return

    session = SessionLocal()
    try:
        existing_roles = session.query(Role).all()
        if not existing_roles:
            print("[DB] Adding default roles...")
            roles = [
                Role(name='Superadmin'),
                Role(name='Admin'),
                Role(name='User')
            ]
            session.add_all(roles)
            session.commit()
            print("[DB] Default roles added successfully.")
        else:
            print(f"[DB] Roles already exist: {[r.name for r in existing_roles]}")
    except Exception as e:
        session.rollback()
        print(f"[DB][Error] Failed to initialize default roles: {e}")
    finally:
        session.close()
# -------------------------
# Helper function to get session
# -------------------------
def get_session():
    try:
        session = SessionLocal()
        return session
    except Exception as e:
        print(f"[DB][Error] Failed to create session: {e}")
        return None
