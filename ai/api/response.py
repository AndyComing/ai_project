"""
统一响应格式工具类
提供RESTful风格的标准响应格式
"""
from datetime import datetime
from typing import Any, Optional, Dict, List
from fastapi import status
from fastapi.responses import JSONResponse


class ResponseFormat:
    """统一响应格式"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: str = "200"
    ) -> Dict[str, Any]:
        """成功响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(
        message: str = "操作失败",
        code: str = "500",
        data: Any = None
    ) -> Dict[str, Any]:
        """错误响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "创建成功",
        code: str = "201"
    ) -> Dict[str, Any]:
        """创建成功响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def updated(
        data: Any = None,
        message: str = "更新成功",
        code: str = "200"
    ) -> Dict[str, Any]:
        """更新成功响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def deleted(
        data: Any = None,
        message: str = "删除成功",
        code: str = "200"
    ) -> Dict[str, Any]:
        """删除成功响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def unauthorized(
        message: str = "未授权访问",
        code: str = "401",
        data: Any = None
    ) -> Dict[str, Any]:
        """未授权响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def forbidden(
        message: str = "权限不足",
        code: str = "403",
        data: Any = None
    ) -> Dict[str, Any]:
        """权限不足响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def not_found(
        message: str = "资源不存在",
        code: str = "404",
        data: Any = None
    ) -> Dict[str, Any]:
        """资源不存在响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }
    
    @staticmethod
    def validation_error(
        message: str = "参数验证失败",
        code: str = "400",
        data: Any = None
    ) -> Dict[str, Any]:
        """参数验证失败响应格式"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timetemp": datetime.now().isoformat()
        }

    @staticmethod
    def paginated_success(
        items: List[Any],
        total: int,
        page: int,
        size: int,
        message: str = "查询成功",
        code: str = "200"
    ) -> Dict[str, Any]:
        """分页查询成功响应格式"""
        pages = (total + size - 1) // size  # 计算总页数
        
        return {
            "code": code,
            "message": message,
            "data": {
                "list": items,      # 使用 "list" 而不是 "items"
                "total": total,
                "page": page,
                "size": size,
                "pages": pages      # 添加总页数
            },
            "timetemp": datetime.now().isoformat()
        }


class APIResponse:
    """API响应工具类"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: str = "200",
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """成功响应"""
        content = ResponseFormat.success(data=data, message=message, code=code)
        return JSONResponse(content=content, status_code=status_code)
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "创建成功",
        code: str = "201"
    ) -> JSONResponse:
        """创建成功响应"""
        content = ResponseFormat.created(data=data, message=message, code=code)
        return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)
    
    @staticmethod
    def updated(
        data: Any = None,
        message: str = "更新成功",
        code: str = "200"
    ) -> JSONResponse:
        """更新成功响应"""
        content = ResponseFormat.updated(data=data, message=message, code=code)
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)
    
    @staticmethod
    def deleted(
        data: Any = None,
        message: str = "删除成功",
        code: str = "200"
    ) -> JSONResponse:
        """删除成功响应"""
        content = ResponseFormat.deleted(data=data, message=message, code=code)
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)
    
    @staticmethod
    def error(
        message: str = "操作失败",
        code: str = "500",
        data: Any = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> JSONResponse:
        """错误响应"""
        content = ResponseFormat.error(message=message, code=code, data=data)
        return JSONResponse(content=content, status_code=status_code)
    
    @staticmethod
    def unauthorized(
        message: str = "未授权访问",
        code: str = "401",
        data: Any = None
    ) -> JSONResponse:
        """未授权响应"""
        content = ResponseFormat.unauthorized(message=message, code=code, data=data)
        return JSONResponse(content=content, status_code=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def forbidden(
        message: str = "权限不足",
        code: str = "403",
        data: Any = None
    ) -> JSONResponse:
        """权限不足响应"""
        content = ResponseFormat.forbidden(message=message, code=code, data=data)
        return JSONResponse(content=content, status_code=status.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def not_found(
        message: str = "资源不存在",
        code: str = "404",
        data: Any = None
    ) -> JSONResponse:
        """资源不存在响应"""
        content = ResponseFormat.not_found(message=message, code=code, data=data)
        return JSONResponse(content=content, status_code=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def validation_error(
        message: str = "参数验证失败",
        code: str = "400",
        data: Any = None
    ) -> JSONResponse:
        """参数验证失败响应"""
        content = ResponseFormat.validation_error(message=message, code=code, data=data)
        return JSONResponse(content=content, status_code=status.HTTP_400_BAD_REQUEST) 


class StandardResponse:
    """标准HTTP响应格式"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        status_code: int = 200
    ) -> Dict[str, Any]:
        """标准成功响应格式"""
        return {
            "success": True,
            "status_code": status_code,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(
        message: str = "操作失败",
        status_code: int = 500,
        data: Any = None,
        error_code: str = None
    ) -> Dict[str, Any]:
        """标准错误响应格式"""
        response = {
            "success": False,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            response["data"] = data
        if error_code:
            response["error_code"] = error_code
            
        return response
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "创建成功"
    ) -> Dict[str, Any]:
        """创建成功响应格式"""
        return StandardResponse.success(data=data, message=message, status_code=201)
    
    @staticmethod
    def updated(
        data: Any = None,
        message: str = "更新成功"
    ) -> Dict[str, Any]:
        """更新成功响应格式"""
        return StandardResponse.success(data=data, message=message, status_code=200)
    
    @staticmethod
    def deleted(
        data: Any = None,
        message: str = "删除成功"
    ) -> Dict[str, Any]:
        """删除成功响应格式"""
        return StandardResponse.success(data=data, message=message, status_code=200)
    
    @staticmethod
    def not_found(
        message: str = "资源不存在",
        error_code: str = "RESOURCE_NOT_FOUND"
    ) -> Dict[str, Any]:
        """资源不存在响应格式"""
        return StandardResponse.error(message=message, status_code=404, error_code=error_code)
    
    @staticmethod
    def validation_error(
        message: str = "参数验证失败",
        data: Any = None,
        error_code: str = "VALIDATION_ERROR"
    ) -> Dict[str, Any]:
        """参数验证失败响应格式"""
        return StandardResponse.error(message=message, status_code=400, data=data, error_code=error_code)
    
    @staticmethod
    def unauthorized(
        message: str = "未授权访问",
        error_code: str = "UNAUTHORIZED"
    ) -> Dict[str, Any]:
        """未授权响应格式"""
        return StandardResponse.error(message=message, status_code=401, error_code=error_code)
    
    @staticmethod
    def forbidden(
        message: str = "权限不足",
        error_code: str = "FORBIDDEN"
    ) -> Dict[str, Any]:
        """权限不足响应格式"""
        return StandardResponse.error(message=message, status_code=403, error_code=error_code) 