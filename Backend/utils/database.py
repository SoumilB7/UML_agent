import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Default to localhost if not provided
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "uml_agent"

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def get_database():
    """
    Return the database instance. 
    Initializes the connection if it doesn't exist.
    """
    if db.client is None:
        db.client = AsyncIOMotorClient(MONGODB_URL)
    return db.client[DATABASE_NAME]

async def close_mongo_connection():
    """Close the MongoDB connection."""
    if db.client:
        db.client.close()
        db.client = None
