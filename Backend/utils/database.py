import os
import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Default to localhost if not provided
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "uml_agent"

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def get_database():
    """
    Return the database instance. 
    Initializes the connection if it doesn't exist.
    """
    if db.client is None:
        # Log the URL being used (masking password)
        masked_url = MONGODB_URL
        if "@" in MONGODB_URL:
            prefix = MONGODB_URL.split("@")[0].split(":")[0] # mongodb+srv://user
            suffix = MONGODB_URL.split("@")[1]
            masked_url = f"{prefix}:****@{suffix}"
        
        logger.info(f"Connecting to MongoDB at: {masked_url}")
        
        # Use certifi for SSL certificate verification (crucial for Vercel/AWS Lambda)
        db.client = AsyncIOMotorClient(
            MONGODB_URL,
            tlsCAFile=certifi.where()
        )
    return db.client[DATABASE_NAME]

async def close_mongo_connection():
    """Close the MongoDB connection."""
    if db.client:
        db.client.close()
        db.client = None
