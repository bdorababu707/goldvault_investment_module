import uuid

async def generate_uuid() -> str:
    return str(uuid.uuid4())
