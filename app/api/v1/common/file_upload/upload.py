from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import List

from app.core.security import get_current_admin
from app.models.base import OutModel
from app.schemas.common.utils.s3.upload import FileTypeEnum, SingleFileUploadResponse
from app.services.common.utils.s3.upload import S3FileUploadService


router = APIRouter(prefix="/upload", tags=["File Upload"])


# @router.post("/files/")
# async def upload_mutipile_files(file_type: FileTypeEnum = Form(...), files: List[UploadFile] = File(...), current_user = Depends(get_current_user)):
#     try:

#         if S3FileUploadService.has_valid_files(files):

#             allowed_extensions = S3FileUploadService.get_allowed_extensions()

#             response = await S3FileUploadService.upload_multiple_files(
#                 files=files,
#                 user_id=current_user["uuid"],
#                 file_type=file_type,
#                 allowed_extensions=allowed_extensions,
#             )

#             return response

#         else:@router.post("/files/")
# async def upload_mutipile_files(file_type: FileTypeEnum = Form(...), files: List[UploadFile] = File(...), current_user = Depends(get_current_user)):
#     try:

#         if S3FileUploadService.has_valid_files(files):

#             allowed_extensions = S3FileUploadService.get_allowed_extensions()

#             response = await S3FileUploadService.upload_multiple_files(
#                 files=files,
#                 user_id=current_user["uuid"],
#                 file_type=file_type,
#                 allowed_extensions=allowed_extensions,
#             )

#             return response

#         else:
#             return OutModel(status="error", status_code=400, comment="empty file list", data=None)
    
#     except Exception as err:
#         return OutModel(status="error", status_code=400, comment="something went wrong", data={"error": str(err)})


#             return OutModel(status="error", status_code=400, comment="empty file list", data=None)
    
#     except Exception as err:
#         return OutModel(status="error", status_code=400, comment="something went wrong", data={"error": str(err)})



@router.post("/file/")
async def upload_single_file(file_type: FileTypeEnum = Form(...), file: UploadFile = File(...),user_email: str = Form(...), current_user = Depends(get_current_admin)):
    try:

        if S3FileUploadService.has_valid_files([file]):
            
            allowed_extensions = S3FileUploadService.get_allowed_extensions()

            response = await S3FileUploadService.upload_single_file(
                file=file,
                user_email=user_email,
                file_type=file_type,
                allowed_extensions=allowed_extensions,
            )

            if response["success"]:
                upload_data = SingleFileUploadResponse(
                    filename=response["original_filename"],
                    file_url=response["file_url"]
                )


                return OutModel(status="success", status_code=200, comment="file uploaded successfully", data={"upload_data": upload_data})

            else:
                return OutModel(status="error", status_code=400, comment="upload failed, check data for more details", data={"error": response["error"]})
        
        else:
            return OutModel(status="error", status_code=400, comment="empty file, please provide a file", data=None)
    
    except Exception as err:
        return OutModel(status="error", status_code=400, comment="something went wrong", data={"error": str(err)})