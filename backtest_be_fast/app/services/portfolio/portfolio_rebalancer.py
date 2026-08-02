"""포트폴리오 리밸런싱 관리

리밸런싱 거래 실행, 상장폐지 종목 반영한 목표 비중 조정, 거래 내역 기록을 담당합니다.
"""

import logging
from typing import Dict, Any, Iterable, Set, Tuple
from app.domain.portfolio_domain import DcaStrategyInfo

logger = logging.getLogger(__name__)


class PortfolioRebalancer:
    """포트폴리오 리밸런싱 관리 클래스"""

    @staticmethod
    def _colliding_symbols(
        unique_keys: Iterable[str],
        dca_info: Dict[str, DcaStrategyInfo]
    ) -> Set[str]:
        """
        [P3-29] 주어진 unique_key 집합 중, 표시 심볼(symbol)이 2개 이상의
        unique_key에서 공유되는 심볼 집합을 찾는다.

        예: 이름이 같은 현금 항목을 두 개 추가하면(스키마가 현금은 이름 중복
        검증에서 제외) 'CASH__cash_1'과 'CASH__cash_2'가 둘 다 symbol='CASH'를
        가리킨다 -- 이 경우 {'CASH'}가 반환된다. 주식은 unique_key가 항상
        symbol과 동일하므로(portfolio_manager_service.py) 실제로는 충돌이
        생기지 않는다.
        """
        symbol_counts: Dict[str, int] = {}
        for unique_key in unique_keys:
            if unique_key not in dca_info:
                continue
            symbol = dca_info[unique_key].symbol
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        return {symbol for symbol, count in symbol_counts.items() if count > 1}

    def calculate_adjusted_weights(
        self,
        target_weights: Dict[str, float],
        delisted_stocks: set,
        dca_info: Dict[str, DcaStrategyInfo]
    ) -> Dict[str, float]:
        """
        상장폐지 종목이 있을 경우 목표 비중을 동적으로 조정합니다.

        상장폐지 종목의 비중을 0으로 설정하고,
        거래 가능한 종목들의 비중을 비례적으로 증가시킵니다.

        Args:
            target_weights: 원래 목표 비중
            delisted_stocks: 상장폐지된 종목 세트
            dca_info: 분할 매수 정보 (로깅용)

        Returns:
            조정된 목표 비중 딕셔너리
        """
        # 상장폐지 종목이 없으면 원본 그대로 반환
        if not delisted_stocks:
            return dict(target_weights)

        # 상장폐지 종목들의 원래 목표 비중 합계
        delisted_weight_sum = sum(
            target_weights[key] for key in delisted_stocks if key in target_weights
        )

        # 상장폐지 비중이 없으면 원본 그대로
        if delisted_weight_sum <= 0:
            return dict(target_weights)

        # 거래 가능한 종목들의 원래 비중 합계
        tradeable_weight_sum = 1.0 - delisted_weight_sum

        # 거래 가능한 종목이 없으면 원본 그대로
        if tradeable_weight_sum <= 0:
            return dict(target_weights)

        # 거래 가능한 종목들의 비중을 비례적으로 증가
        scaling_factor = 1.0 / tradeable_weight_sum
        adjusted_target_weights = {}

        for unique_key, original_weight in target_weights.items():
            if unique_key in delisted_stocks:
                # 상장폐지 종목은 목표 비중을 0으로 (거래 불가)
                adjusted_target_weights[unique_key] = 0.0
            else:
                # 거래 가능한 종목은 비중을 비례적으로 증가
                adjusted_target_weights[unique_key] = original_weight * scaling_factor

        logger.info(
            f"리밸런싱 목표 비중 동적 조정: 상장폐지 종목 {len(delisted_stocks)}개 "
            f"(원래 비중 합계: {delisted_weight_sum:.2%}) -> "
            f"거래 가능 종목 비중 {scaling_factor:.2f}배 증가"
        )

        # 조정된 비중 로깅
        for unique_key in delisted_stocks:
            if unique_key in target_weights:
                symbol = dca_info[unique_key].symbol
                logger.debug(
                    f"  {symbol}: {target_weights[unique_key]:.2%} -> 0.00% (상장폐지)"
                )

        return adjusted_target_weights

    def execute_rebalancing_trades(
        self,
        current_date,  # pd.Timestamp
        adjusted_target_weights: Dict[str, float],
        shares: Dict[str, float],
        current_prices: Dict[str, float],
        available_cash: float,
        cash_holdings: Dict[str, float],
        commission: float,
        total_stock_value: float,
        dca_info: Dict[str, DcaStrategyInfo],
        delisted_stocks: set,
        trading_thresholds=None  # TradingThresholds
    ) -> Dict[str, Any]:
        """
        리밸런싱 거래를 실행하고 히스토리를 기록합니다.

        **역할**:
        - 목표 비중에 맞춰 주식 및 현금 자산 재조정
        - 상장폐지 종목 거래 제외 (보유 유지)
        - 거래 수수료 적용 및 비례 축소
        - 거래 내역 및 비중 변화 기록

        **파라미터**:
        - current_date: 현재 시뮬레이션 날짜
        - adjusted_target_weights: 조정된 목표 비중 (상장폐지 반영)
        - shares: 종목별 보유 주식 수
        - current_prices: 종목별 현재 가격
        - available_cash: 사용 가능한 현금
        - cash_holdings: 현금 자산별 보유액
        - commission: 거래 수수료
        - total_stock_value: 주식 자산 총 가치
        - dca_info: 종목 정보 (DcaStrategyInfo 모델)
        - delisted_stocks: 상장폐지 종목 집합
        - trading_thresholds: 거래 임계값 설정

        **반환**:
        - trades_executed: 실행된 거래 수
        - rebalance_trades: 거래 내역 리스트
        - weights_before: 리밸런싱 전 비중
        - weights_after: 리밸런싱 후 비중
        - commission_cost: 총 수수료 비용
        - updated_shares: 업데이트된 주식 보유량
        - updated_cash_holdings: 업데이트된 현금 보유액
        - updated_available_cash: 업데이트된 사용 가능 현금
        """
        # TradingThresholds import를 피하기 위해 파라미터로 받음
        if trading_thresholds is None:
            from app.constants.data_loading import TradingThresholds
            trading_thresholds = TradingThresholds

        total_portfolio_value = total_stock_value + available_cash

        if total_portfolio_value <= 0:
            return {
                'trades_executed': 0,
                'rebalance_trades': [],
                'weights_before': {},
                'weights_after': {},
                'commission_cost': 0.0,
                'updated_shares': shares,
                'updated_cash_holdings': cash_holdings,
                'updated_available_cash': available_cash
            }

        # [P3-29] weights_before/weights_after의 리포트 키: 심볼이 겹치지
        # 않는 한(실무에서 거의 항상 그렇다) 기존처럼 표시 심볼을 그대로 쓴다.
        # 같은 심볼을 가리키는 unique_key가 둘 이상이면(예: 이름이 같은 현금
        # 항목을 여러 개 추가한 경우) 그 심볼들만 unique_key로 폴백해 서로
        # 다른 항목이 이 리포트 딕셔너리 안에서 충돌해 사라지지 않도록 한다.
        # (total_portfolio_value, individual_returns 등은 원래부터 unique_key
        # 기반이라 이 충돌의 영향을 받지 않았다 -- 이건 리포트 표시만의 문제다.)
        report_participant_keys = set(shares.keys()) | set(cash_holdings.keys())
        colliding_symbols = self._colliding_symbols(report_participant_keys, dca_info)

        def _report_key(unique_key: str) -> str:
            symbol = dca_info[unique_key].symbol
            return unique_key if symbol in colliding_symbols else symbol

        # 리밸런싱 전 비중 계산 (현금 포함)
        weights_before = {}
        for unique_key in shares.keys():
            if unique_key in current_prices:
                current_value = shares[unique_key] * current_prices[unique_key]
                weights_before[_report_key(unique_key)] = current_value / total_portfolio_value
        # 현금 비중 추가
        for unique_key in cash_holdings.keys():
            weights_before[_report_key(unique_key)] = cash_holdings[unique_key] / total_portfolio_value

        # 상장폐지 종목은 거래 없이 보유만 유지되므로, 재분배 대상 풀(pool)에서
        # 그 가치를 제외해야 한다. 그렇지 않으면 total_portfolio_value(상장폐지
        # 종목의 가치를 포함한 값)를 거래 가능 종목에게 그대로 재분배 비율로
        # 곱하면서, 상장폐지 종목이 그대로 보유 유지하는 가치가 한 번 더
        # 더해져(이중 계산) 리밸런싱마다 포트폴리오 총 가치가 상장폐지 종목의
        # 가치만큼 부풀려진다 (가격 정보가 없으면 0으로 처리, 기존 로직과 동일).
        delisted_value = sum(
            shares.get(unique_key, 0) * current_prices.get(unique_key, 0)
            for unique_key in delisted_stocks
        )
        allocatable_pool_value = max(0.0, total_portfolio_value - delisted_value)

        # 목표 비중대로 재조정 (조정된 비중 사용, 상장폐지 가치를 제외한 풀 기준)
        new_shares = {}
        new_cash_holdings = {}
        total_commission_cost = 0
        trades_in_rebalance = 0
        rebalance_trades = []  # 이번 리밸런싱의 거래 내역

        for unique_key, target_weight in adjusted_target_weights.items():
            target_value = allocatable_pool_value * target_weight

            # 현금 처리
            if dca_info[unique_key].asset_type == 'cash':
                current_value = cash_holdings.get(unique_key, 0)
                # 현금은 거래 수수료 없이 조정
                new_cash_holdings[unique_key] = target_value

                # 현금 조정 내역 기록 (차이가 있을 때만)
                if abs(target_value - current_value) / total_portfolio_value > trading_thresholds.REBALANCING_THRESHOLD_PCT:
                    trades_in_rebalance += 1
                    symbol = dca_info[unique_key].symbol
                    if target_value > current_value:
                        rebalance_trades.append({
                            'symbol': symbol,
                            'action': 'increase',  # 현금 증가 (주식 매도)
                            'amount': abs(target_value - current_value),
                            'price': 1.0
                        })
                    else:
                        rebalance_trades.append({
                            'symbol': symbol,
                            'action': 'decrease',  # 현금 감소 (주식 매수)
                            'amount': abs(target_value - current_value),
                            'price': 1.0
                        })

            # 주식 처리
            else:
                # 상장폐지 종목은 보유 주식 수 유지 (거래 불가)
                if unique_key in delisted_stocks:
                    new_shares[unique_key] = shares[unique_key]
                    current_price = current_prices.get(unique_key, 0)
                    symbol = dca_info[unique_key].symbol

                    if current_price == 0:
                        logger.warning(
                            f"  {symbol} 상장폐지 종목: 가격 정보 없음, "
                            f"보유 주식 {shares[unique_key]:.4f}주만 유지"
                        )
                    else:
                        current_value = shares[unique_key] * current_price
                        logger.debug(
                            f"  {symbol} 상장폐지 종목: 보유 주식 {shares[unique_key]:.4f}주 유지 "
                            f"(가치: ${current_value:,.2f}, 리밸런싱 불가)"
                        )
                    continue

                if unique_key not in current_prices:
                    new_shares[unique_key] = shares[unique_key]
                    continue

                price = current_prices[unique_key]
                current_value = shares[unique_key] * price
                symbol = dca_info[unique_key].symbol

                # 매도/매수가 발생했는지 확인 (0.01% 이상 차이나면 거래로 간주)
                if abs(target_value - current_value) / total_portfolio_value > trading_thresholds.REBALANCING_THRESHOLD_PCT:
                    trades_in_rebalance += 1

                    # 거래 내역 기록
                    shares_diff = (target_value / price) - shares[unique_key]
                    if shares_diff > 0:
                        rebalance_trades.append({
                            'symbol': symbol,
                            'action': 'buy',
                            'shares': abs(shares_diff),
                            'price': price
                        })
                    else:
                        rebalance_trades.append({
                            'symbol': symbol,
                            'action': 'sell',
                            'shares': abs(shares_diff),
                            'price': price
                        })

                # 매도/매수 금액
                trade_value = abs(target_value - current_value)
                commission_cost = trade_value * commission
                total_commission_cost += commission_cost

                # 새로운 주식 수 계산
                new_shares[unique_key] = target_value / price

        # 수수료만큼 전체적으로 비례 축소
        # [P3-27] 상장폐지 종목은 거래가 불가능하므로 보유 주식 수가 리밸런싱으로
        # 절대 변하면 안 된다. total_commission_cost는 거래 가능 자산(주식 매매)
        # 에서만 발생한다 -- 상장폐지 종목은 위에서 target_value/commission 계산
        # 전에 continue로 건너뛰어 commission_cost에 전혀 기여하지 않는다. 따라서
        # 수수료도 거래 가능 자산 풀(거래 가능 주식 + 현금)에서만 차감해야 한다.
        # 상장폐지 종목까지 포함한 total_portfolio_value를 축소 기준으로 쓰면,
        # 매 리밸런싱마다 상장폐지 종목의 보유 주식 수가 (작지만 0이 아닌 만큼)
        # 계속 줄어드는 오류가 생긴다.
        tradeable_value = sum(
            new_shares[k] * current_prices[k]
            for k in new_shares.keys()
            if k not in delisted_stocks and k in current_prices
        ) + sum(new_cash_holdings.values())

        if tradeable_value > total_commission_cost and tradeable_value > 0:
            scale_factor = (tradeable_value - total_commission_cost) / tradeable_value
        else:
            # 수수료가 거래 가능 자산 가치를 넘어서거나(비정상적으로 큰 수수료)
            # 거래 가능 자산이 아예 없는 경우(전량 상장폐지 + 현금 없음) -- 기존
            # 코드와 동일하게 축소 없이 그대로 둔다 (음수/0-나눗셈 방지).
            scale_factor = 1.0

        updated_shares = {
            k: (v if k in delisted_stocks else v * scale_factor)
            for k, v in new_shares.items()
        }
        updated_cash_holdings = {k: v * scale_factor for k, v in new_cash_holdings.items()}
        updated_available_cash = sum(updated_cash_holdings.values())

        # 리밸런싱 후 비중 계산 (현금 포함)
        weights_after = {}
        new_total_stock_value = sum(
            updated_shares[key] * current_prices[key]
            for key in updated_shares.keys()
            if key in current_prices
        )
        new_total_portfolio_value = new_total_stock_value + updated_available_cash

        for unique_key in updated_shares.keys():
            if unique_key in current_prices:
                new_value = updated_shares[unique_key] * current_prices[unique_key]
                weights_after[_report_key(unique_key)] = new_value / new_total_portfolio_value
        # 현금 비중 추가 (weights_before와 동일한 collision 판정을 재사용해
        # 같은 unique_key가 before/after에서 항상 같은 리포트 키로 나오게 한다)
        for unique_key in updated_cash_holdings.keys():
            weights_after[_report_key(unique_key)] = updated_cash_holdings[unique_key] / new_total_portfolio_value

        # 리밸런싱 거래 상세 로깅
        if rebalance_trades:
            logger.info(
                f"{current_date.date()}: 리밸런싱 완료 "
                f"(거래 {trades_in_rebalance}건, 수수료 ${total_commission_cost:.2f})"
            )
            for trade in rebalance_trades:
                if 'shares' in trade:  # 주식 거래
                    logger.debug(
                        f"  - {trade['action'].upper()} {trade['symbol']}: "
                        f"{trade['shares']:.4f} 주 @ ${trade['price']:.2f}"
                    )
                else:  # 현금 조정
                    logger.debug(
                        f"  - {trade['action'].upper()} {trade['symbol']}: "
                        f"${trade['amount']:.2f}"
                    )
        else:
            logger.debug(f"{current_date.date()}: 리밸런싱 날짜이지만 거래 불필요 (이미 균형 잡힘)")

        return {
            'trades_executed': trades_in_rebalance,
            'rebalance_trades': rebalance_trades,
            'weights_before': weights_before,
            'weights_after': weights_after,
            'commission_cost': total_commission_cost,
            'updated_shares': updated_shares,
            'updated_cash_holdings': updated_cash_holdings,
            'updated_available_cash': updated_available_cash
        }
