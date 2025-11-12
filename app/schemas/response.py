"""
Common response schemas for API endpoints
"""
from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

DataType = TypeVar('DataType')


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None


class DataResponse(BaseResponse, Generic[DataType]):
    """Response model with data"""
    data: DataType


class ListResponse(BaseResponse, Generic[DataType]):
    """Response model for paginated lists"""
    data: List[DataType]
    pagination: Optional[Dict[str, Any]] = None


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseResponse, Generic[DataType]):
    """Response model for paginated data"""
    data: List[DataType]
    pagination: PaginationInfo


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"
    services: Optional[Dict[str, str]] = None


class FileUploadResponse(BaseResponse):
    """File upload response"""
    data: Dict[str, Any] = Field(..., description="File upload information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "File uploaded successfully",
                "data": {
                    "filename": "model.stl",
                    "size": 1024000,
                    "url": "/uploads/model.stl",
                    "content_type": "application/octet-stream"
                }
            }
        }
    )


class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    type: str
    severity: str
    title: str
    message: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any]


class SystemStatusResponse(BaseModel):
    """System status response"""
    timestamp: str
    system: Dict[str, Any]
    alerts: Dict[str, Any]
    uptime: Dict[str, Any]