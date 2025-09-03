from fastapi import APIRouter
from app.api.endpoints import backtest, stock

api_router = APIRouter()
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(stock.router, prefix="/stock", tags=["stock"]) 