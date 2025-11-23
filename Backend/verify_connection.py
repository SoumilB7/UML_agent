import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

async def verify_connection():
    url = os.getenv("MONGODB_URL")
    print(f"Testing connection to: {url.split('@')[-1] if '@' in url else 'LOCAL'}")
    
    try:
        client = AsyncIOMotorClient(url)
        # The ismaster command is cheap and does not require auth.
        # To test auth, we need to run a command that requires it, like list_collection_names or ping
        await client.admin.command('ping')
        print("SUCCESS: Connected and authenticated successfully!")
        
        # Check database access
        db = client.get_database("uml_agent")
        collections = await db.list_collection_names()
        print(f"Available collections: {collections}")
        
    except Exception as e:
        print(f"FAILURE: Connection failed.")
        print(f"Error: {str(e)}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(verify_connection())
