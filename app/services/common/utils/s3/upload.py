import os
import uuid
import asyncio
import aioboto3

from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.models.base import OutModel
from app.schemas.common.utils.s3.upload import MultiFileUploadResponse


logger = get_logger(__name__)


class S3FileUploadService:
    """Simplified AWS S3 file upload service with async support"""


    @staticmethod
    def get_session():
        """Get aioboto3 session with credentials from environment"""
        return aioboto3.Session(
            aws_access_key_id = settings.S3_CREDENTIALS.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = settings.S3_CREDENTIALS.AWS_SECRET_ACCESS_KEY,
            region_name = settings.S3_CREDENTIALS.AWS_REGION
        )


    @staticmethod
    def get_path(user_email: str, file_type: str, filename: str, base: str) -> str:

        # Clean up path components
        base = base.strip().strip('/')
        user_email = str(user_email).strip().strip('/')
        file_type = file_type.strip().strip('/').lower()
        filename = filename.strip().strip('/')

        file_path = f"{base}/{user_email}/{file_type}/{filename}"

        return file_path


    @staticmethod
    @lru_cache(maxsize=1)  # Cache only 1 result since we only have 1 env var
    def get_allowed_extensions() -> List[str]:
        
        extensions_str = settings.S3_CREDENTIALS.ALLOWED_FILE_EXTENSIONS
        if not extensions_str:
            return []
        
        # Split by comma and clean up
        extensions = [ext.strip() for ext in extensions_str.split(",") if ext.strip()]
        
        # Ensure extensions start with dot
        normalized = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = f'.{ext}'
            normalized.append(ext.lower())
        
        return normalized


    @staticmethod
    async def upload_single_file(
        file: UploadFile,
        user_email: str,
        file_type: str,
        allowed_extensions: Optional[List[str]] = None,
        generate_unique_name: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a single file to S3 bucket with structured path
        
        Args:
            file: FastAPI UploadFile object
            bucket_name: S3 bucket name
            user_id: User ID for folder structure
            file_type: File type for folder structure (e.g., "profile_images", "documents")
            base: Base folder name (default: "app_documents")
            allowed_extensions: List of allowed file extensions (e.g., [".pdf", ".doc", ".jpg"])
            max_size_mb: Maximum file size in MB
            generate_unique_name: Whether to generate unique filename to avoid conflicts
            
        Returns:
            Dict with upload result
        """
        bucket_name = settings.S3_CREDENTIALS.AWS_BUCKET_NAME
        base = settings.S3_CREDENTIALS.BASE_DIR
        max_size_mb = settings.S3_CREDENTIALS.MAX_FILE_SIZE_MB

        file_key = None

        try:
            
            # Validate file
            validation_result = S3FileUploadService.validate_file(file, allowed_extensions, max_size_mb)
            if not validation_result["valid"]:
                logger.warning(f"File validation failed for {file.filename}: {validation_result['error']}")
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "status_code": 400,
                    "file_key": None,
                    "file_url": None
                }
            
            # Generate final filename (with UUID if needed)
            final_filename = S3FileUploadService.generate_unique_filename(file.filename, generate_unique_name)
            
            # Generate file key using internal path method
            file_key = S3FileUploadService.get_path(user_email, file_type, final_filename, base)
            
            # Get file size efficiently for FastAPI UploadFile
            if hasattr(file, 'size') and file.size is not None:
                # FastAPI UploadFile has size attribute
                file_size = file.size
            else:
                # Fallback: read to get size, then reset
                await file.seek(0)
                content = await file.read()
                file_size = len(content)
                await file.seek(0)  # Reset to beginning
                        
            # Upload to S3 directly
            session = S3FileUploadService.get_session()
            async with session.client('s3') as s3_client:
                await s3_client.put_object(
                    Bucket=bucket_name,
                    Key=file_key,
                    Body=file.file  # Pass file object directly
                )
            
            # Generate public URL
            aws_region = os.getenv('AWS_REGION', 'us-east-1')
            file_url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{file_key}"
                        
            return {
                "success": True,
                "file_key": file_key,
                "file_url": file_url,
                "file_size": file_size,
                "bucket": bucket_name,
                "original_filename": file.filename
            }
            
        except NoCredentialsError:
            error_msg = "AWS credentials not found. Please check your environment variables."
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_key": file_key,
                "file_url": None
            }
            
        except ClientError as err:
            error_code = err.response['Error']['Code']
            error_msg = f"AWS S3 error ({error_code}): {err.response['Error']['Message']}"
            logger.error(f"S3 upload failed for {file.filename}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_key": file_key,
                "file_url": None
            }
            
        except Exception as err:
            error_msg = f"Critical error during file upload service, file upload failed: {str(err)}"
            logger.error(f"Critical error during file upload service, file upload failed for filename: {file.filename} of user: {user_email}, error: {err}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "file_key": file_key,
                "file_url": None
            }


    @staticmethod
    async def upload_multiple_files(
        files: List[UploadFile],
        user_id: str,
        file_type: str,
        allowed_extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Upload multiple files to S3 concurrently with structured path
        
        Args:
            files: List of FastAPI UploadFile objects
            bucket_name: S3 bucket name
            user_id: User ID for folder structure
            file_type: File type for folder structure (e.g., "profile_images", "documents")
            base: Base folder name (default: "app_documents")
            allowed_extensions: List of allowed file extensions (e.g., [".pdf", ".doc", ".jpg"])
            max_size_mb: Maximum file size in MB per file
            generate_unique_name: Whether to generate unique filenames
            max_concurrent: Maximum number of concurrent uploads
            
        Returns:
            Dict with upload results for all files
        """

        generate_unique_name = True
        max_concurrent = int(settings.S3_CREDENTIALS.MAX_CONCURRENT_UPLOADS)
                
        # Create semaphore to limit concurrent uploads
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def upload_with_semaphore(file_with_index):
            file, index = file_with_index
            async with semaphore:
                result = await S3FileUploadService.upload_single_file(
                    file=file,
                    user_id=user_id,
                    file_type=file_type,
                    allowed_extensions=allowed_extensions,
                    generate_unique_name=generate_unique_name
                )
                # Add filename to result for safety
                result["original_filename"] = file.filename or f"file_{index}"
                return result
        
        try:
            # Create tasks for concurrent uploads
            tasks = [upload_with_semaphore((file, i)) for i, file in enumerate(files)]
            
            # Execute all uploads concurrently
            upload_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            results = []
            successful_uploads = 0
            failed_uploads = 0
            successful_urls = []
            
            for result in upload_results:
                
                # Handle exceptions
                if isinstance(result, Exception):
                    logger.error(f"Exception during upload: {result}")
                    result = {
                        "success": False,
                        "error": f"Upload exception: {str(result)}",
                        "file_key": None,
                        "file_url": None,
                        "original_filename": "unknown"
                    }
                
                # Get filename from result (now guaranteed to exist)
                filename = result.get("original_filename", "unknown")
                
                # Count successes and failures
                if result.get("success", False):
                    successful_uploads += 1
                    if result.get("file_url"):
                        successful_urls.append(result["file_url"])
                else:
                    failed_uploads += 1
                
                results.append({
                    "filename": filename,
                    "success": result.get("success", False),
                    "file_url": result.get("file_url"),
                    "file_key": result.get("file_key"),
                    "error": result.get("error") if not result.get("success", False) else None,
                    "file_size": result.get("file_size")
                })
                        
            upload_data = MultiFileUploadResponse(
                total_files=len(files),
                successful_uploads=successful_uploads,
                failed_uploads=failed_uploads,
                successful_urls=successful_urls,
                file_data=results
            )
        
            return OutModel(status="success", status_code=200, comment="files uploaded successfully", data={"upload_data": upload_data})
            
        except Exception as err:
            logger.error(f"Critical error during multiple file upload, file upload failed, error: {err}", exc_info=True)
            return OutModel(status="error", status_code=400, comment="Critical error during multiple file upload, file upload failed", data={"error": str(err)})
    

    @staticmethod
    def validate_file(
        file: UploadFile, 
        allowed_extensions: Optional[List[str]], 
        max_size_mb: int
    ) -> Dict[str, Any]:
        """Validate uploaded file for size, extension, and basic requirements"""
        
        # Check if filename exists
        if not file.filename or file.filename.strip() == "":
            return {
                "valid": False,
                "error": "No filename provided"
            }
        
        # Check file size if available
        if hasattr(file, 'size') and file.size is not None:

            # Ensure max_size_mb is an integer
            try:
                max_size_mb = int(max_size_mb)
            except (ValueError, TypeError):
                max_size_mb = 10  # Default fallback
            
            max_size_bytes = max_size_mb * 1024 * 1024
            
            # Ensure file.size is an integer
            try:
                file_size = int(file.size)
            except (ValueError, TypeError):
                return {
                    "valid": False,
                    "error": "Could not determine file size"
                }
            
            if file.size > max_size_bytes:
                # Convert file size to MB for user-friendly message
                file_size_mb = file.size / (1024 * 1024)
                return {
                    "valid": False,
                    "error": f"File size {file_size_mb:.2f}MB exceeds {max_size_mb}MB limit"
                }
                
        # Check file extension if restrictions provided
        if allowed_extensions:
            file_extension = os.path.splitext(file.filename.lower())[1]
            if not file_extension:
                return {
                    "valid": False,
                    "error": "File has no extension"
                }
            if file_extension not in allowed_extensions:
                return {
                    "valid": False,
                    "error": f"File extension '{file_extension}' not allowed. Allowed extensions: {allowed_extensions}"
                }
        
        return {"valid": True}
    

    @staticmethod
    def generate_unique_filename(filename: str, generate_unique_name: bool) -> str:
        """Generate unique filename with optional UUID suffix"""
        
        if generate_unique_name:
            # Split filename into name and extension
            file_name, file_ext = os.path.splitext(filename)
            # Generate UUID and append to original name
            unique_id = uuid.uuid4().hex[:8]  # Use first 8 characters for shorter UUID
            return f"{file_name}_{unique_id}{file_ext.lower()}"
        else:
            # Use original filename (sanitized)
            return filename.replace(" ", "_").replace("(", "").replace(")", "")
    

    @staticmethod
    def has_valid_files(files: List[UploadFile]) -> bool:
        """Check if any valid files were uploaded"""
        return any(
            file.filename and file.filename.strip() and file.size > 0 
            for file in files
        )