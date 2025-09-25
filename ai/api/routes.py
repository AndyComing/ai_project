from fastapi import APIRouter
from api.business import business_router

router = APIRouter()

# 包含业务路由
router.include_router(business_router, prefix="/business", tags=["business"])


