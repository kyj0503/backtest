"""백테스트 히스토리 저장 Repository"""
from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import text

from app.models.requests import BacktestRequest
from app.models.responses import BacktestResult
from app.services.yfinance_db import _get_engine


class BacktestHistoryRepository:
    """백테스트 실행 결과를 영속화하는 Repository"""

    def __init__(self):
        self._engine_factory = _get_engine
        self.logger = logging.getLogger(__name__)

    async def save_history(
        self,
        user_id: int,
        request: BacktestRequest,
        result: BacktestResult,
    ) -> None:
        """백테스트 결과를 backtest_history 테이블에 저장"""
        try:
            engine = self._engine_factory()
            with engine.begin() as conn:
                metrics = self._extract_metrics(result)

                conn.execute(
                    text(
                        """
                        INSERT INTO backtest_history 
                        (user_id, ticker, strategy_name, start_date, end_date, initial_cash,
                         final_value, total_return, sharpe_ratio, max_drawdown,
                         strategy_params, result_data)
                        VALUES (:uid, :ticker, :strategy, :start_date, :end_date, :initial_cash,
                                :final_value, :total_return, :sharpe_ratio, :max_drawdown,
                                :strategy_params, :result_data)
                        """
                    ),
                    {
                        "uid": user_id,
                        "ticker": request.ticker,
                        "strategy": request.strategy,
                        "start_date": request.start_date,
                        "end_date": request.end_date,
                        "initial_cash": request.initial_cash,
                        "final_value": metrics["final_value"],
                        "total_return": metrics["total_return"],
                        "sharpe_ratio": metrics["sharpe_ratio"],
                        "max_drawdown": metrics["max_drawdown"],
                        "strategy_params": self._dump_json(request.strategy_params),
                        "result_data": self._dump_json(result.model_dump()),
                    },
                )
        except Exception as exc:  # pragma: no cover - 방어 로깅
            self.logger.warning("백테스트 히스토리 저장 실패: %s", exc, exc_info=True)

    def _extract_metrics(self, result: BacktestResult) -> dict:
        """결과 객체에서 DB에 저장할 주요 지표 추출"""
        return {
            "final_value": getattr(result, "final_equity", None),
            "total_return": getattr(result, "total_return_pct", None),
            "sharpe_ratio": getattr(result, "sharpe_ratio", None),
            "max_drawdown": getattr(result, "max_drawdown_pct", None),
        }

    def _dump_json(self, payload: Optional[dict]) -> Optional[str]:
        if not payload:
            return None
        return json.dumps(payload, default=str)


# 전역 인스턴스
backtest_history_repository = BacktestHistoryRepository()

