# mongodb.py
import logging
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional, Dict, Any, List
import time 
from app.core.config import settings

# Get logger
logger = logging.getLogger(__name__)

# Global database client and connection
_db_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongodb() -> None:
    """
    Connect to MongoDB using settings from config.
    This should be called once at application startup.
    """
    global _db_client, _db
    
    if _db_client is not None:
        logger.warning("MongoDB connection already established")
        return

    # Get MongoDB settings from config
    mongo_settings = {
        "maxPoolSize": settings.DB.MAX_POOL_SIZE,
        "minPoolSize": settings.DB.MIN_POOL_SIZE,
        "maxIdleTimeMS": settings.DB.MAX_IDLE_TIME_MS,
        "serverSelectionTimeoutMS": settings.DB.SERVER_SELECTION_TIMEOUT_MS,
        "connectTimeoutMS": settings.DB.CONNECT_TIMEOUT_MS
    }
    
    logger.info(f"Connecting to MongoDB at {settings.DB.URL}")
    
    try:
        # Connect to MongoDB
        _db_client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.DB.URL, **mongo_settings
        )
        
        # Verify connection is successful with a ping
        await _db_client.admin.command('ping')
        
        # Get database instance
        _db = _db_client[settings.DB.DB_NAME]
        
        logger.info(f"Connected to MongoDB. Database: {settings.DB.DB_NAME}")
        
        # Log available collections
        collection_names = await _db.list_collection_names()
        logger.debug(f"Available collections: {', '.join(collection_names)}")
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.critical(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def close_mongodb_connection() -> None:
    """
    Close MongoDB connection.
    This should be called once at application shutdown.
    """
    global _db_client
    
    if _db_client is None:
        logger.warning("No MongoDB connection to close")
        return
    
    logger.info("Closing MongoDB connection")
    _db_client.close()
    _db_client = None
    logger.info("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    """
    Get the database instance.
    This function can be used as a dependency in FastAPI.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    
    Raises:
        RuntimeError: If database connection hasn't been established
    """
    if _db is None:
        raise RuntimeError(
            "Database connection not established. "
            "Ensure connect_to_mongodb() is called during startup."
        )
    return _db

async def initialize_collections() -> None:
    """
    Initialize collections and create indices.
    This runs once during application startup.
    """
    db = get_database()
    
    # Create indices for better query performance
    # These operations are idempotent - safe to run multiple times
    
    try:
        # Example: Create index on 'name' field in 'users' collection
        await db[settings.DB_TABLE.USERS].create_index("email", unique=True)
        await db[settings.DB_TABLE.USERS].create_index("phone_number", unique=True)
        
        # # Example: Create compound index
        # await db.products.create_index([
        #     ("category", 1),
        #     ("created_at", -1)  # -1 for descending order
        # ])
        
        logger.info("MongoDB collections and indices initialized")
    except Exception as e:
        logger.error(f"Error initializing MongoDB collections: {str(e)}")
        raise

# Helper functions for common database operations

async def find_one(collection: str, query: Dict[str, Any], projection: Optional[Dict[str, int]] = None) -> Optional[Dict[str, Any]]:
    """Find a single document in the specified collection"""
    db = get_database()
    return await db[collection].find_one(query, projection)

async def find_many(
    collection: str, 
    query: Dict[str, Any], 
    skip: int = 0, 
    limit: int = 100,
    sort: List[tuple] = None,
    projection: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """Find multiple documents in the specified collection"""
    db = get_database()
    cursor = db[collection].find(query, projection).skip(skip).limit(limit)
    
    if sort:
        cursor = cursor.sort(sort)
        
    return await cursor.to_list(length=limit)

async def insert_one(collection: str, document: Dict[str, Any]) -> str:
    """Insert a document into the specified collection"""
    db = get_database()
    result = await db[collection].insert_one(document)
    return str(result.inserted_id)

async def update_one(
    collection: str, 
    query: Dict[str, Any], 
    update: Dict[str, Any],
    upsert: bool = False
) -> int:
    """Update a document in the specified collection"""
    db = get_database()
    result = await db[collection].update_one(query, update, upsert=upsert)

    if result.modified_count > 0:
        await db[collection].update_one(query, {"$set": {"updated_at": int(time.time())}})
        
    return result.modified_count

async def delete_one(collection: str, query: Dict[str, Any]) -> int:
    """Delete a document from the specified collection"""
    db = get_database()
    result = await db[collection].delete_one(query)
    return result.deleted_count

async def aggregate(collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run an aggregation pipeline on the specified collection"""
    db = get_database()
    return await db[collection].aggregate(pipeline).to_list(length=None)