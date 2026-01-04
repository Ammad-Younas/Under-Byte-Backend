from sqlmodel import SQLModel, create_engine, Session

import os

# Use /tmp for Vercel/Serverless environment as root is read-only
# Note: Data in /tmp is ephemeral and will be lost on restart.
if os.environ.get("VERCEL"):
    sqlite_file_name = "/tmp/database.db"
else:
    sqlite_file_name = "database.db"

sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
