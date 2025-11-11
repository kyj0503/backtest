# 기술적 분석 전략 가이드

## 개요

본 시스템은 `backtesting.py` 라이브러리의 `Strategy` 클래스를 상속받아 다양한 기술적 분석 전략을 구현합니다. 모든 전략은 `app/strategies/strategies.py` 파일에 통합되어 있으며, 공통적인 포지션 관리 로직을 위해 `PositionSizingMixin`을 사용합니다.

### 공통 로직: `PositionSizingMixin`

모든 전략은 이 Mixin을 상속받아 일관된 방식으로 포지션을 관리합니다.

-   **역할**: 현재 자산(`equity`)을 기준으로 정해진 비율만큼의 포지션 크기를 계산하고 매수를 실행합니다.
-   **주요 파라미터**:
    -   `position_size` (기본값: `0.95`): 한 번의 거래에 사용할 자산의 비율입니다. 95%를 기본값으로 사용하여 약간의 현금을 남겨 수수료나 슬리피지에 대응합니다.
-   **핵심 메서드**: `calculate_and_buy()`
    -   이 메서드를 호출하면 `position_size`에 맞춰 매수할 주식 수를 자동으로 계산하고 `self.buy()`를 실행합니다.

---

## 지원 전략 목록

### 1. Buy & Hold (매수 후 보유)

-   **전략명**: `buy_hold_strategy`
-   **설명**: 가장 기본적인 투자 전략으로, 백테스트 시작 시점에 가용 자산 전체를 매수하여 기간이 끝날 때까지 보유합니다. 다른 모든 전략의 성과를 비교하는 기준(Benchmark)으로 사용됩니다.
-   **매매 규칙**:
    -   **매수**: 백테스트 첫 번째 봉(bar)에서 즉시 매수합니다.
    -   **매도**: 백테스트 기간이 종료될 때까지 매도하지 않습니다.

### 2. SMA Crossover (단순이동평균 교차)

-   **전략명**: `sma_cross_strategy`
-   **설명**: 단기 이동평균선과 장기 이동평균선의 교차를 이용한 전형적인 추세 추종 전략입니다.
-   **주요 파라미터**:
    -   `sma_short` (기본값: `10`): 단기 이동평균선 기간.
    -   `sma_long` (기본값: `20`): 장기 이동평균선 기간.
-   **매매 규칙**:
    -   **매수 (골든 크로스)**: 단기 이평선(`sma_short`)이 장기 이평선(`sma_long`)을 상향 돌파할 때.
    -   **매도 (데드 크로스)**: 단기 이평선이 장기 이평선을 하향 돌파할 때.

### 3. EMA Crossover (지수이동평균 교차)

-   **전략명**: `ema_strategy`
-   **설명**: SMA와 유사하지만, 최근 가격에 더 높은 가중치를 부여하는 지수이동평균(EMA)을 사용합니다. 가격 변화에 더 민감하게 반응합니다.
-   **주요 파라미터**:
    -   `fast_window` (기본값: `12`): 단기 EMA 기간.
    -   `slow_window` (기본값: `26`): 장기 EMA 기간.
-   **매매 규칙**:
    -   **매수**: 단기 EMA(`fast_window`)가 장기 EMA(`slow_window`)를 상향 돌파할 때.
    -   **매도**: 단기 EMA가 장기 EMA를 하향 돌파할 때.

### 4. RSI (상대강도지수)

-   **전략명**: `rsi_strategy`
-   **설명**: 가격의 상승 압력과 하락 압력 간의 상대적인 강도를 나타내는 모멘텀 지표입니다. 과매도/과매수 구간을 활용한 반전 매매 전략에 주로 사용됩니다.
-   **주요 파라미터**:
    -   `rsi_period` (기본값: `14`): RSI 계산 기간.
    -   `rsi_overbought` (기본값: `70`): 과매수 구간으로 판단하는 기준선.
    -   `rsi_oversold` (기본값: `30`): 과매도 구간으로 판단하는 기준선.
-   **매매 규칙**:
    -   **매수**: RSI 지수가 과매도 기준선(`rsi_oversold`) 아래로 떨어졌을 때.
    -   **매도**: RSI 지수가 과매수 기준선(`rsi_overbought`) 위로 올라가거나, 중립선인 50을 상향 돌파하여 추세가 회복되었다고 판단될 때.

### 5. Bollinger Bands (볼린저 밴드)

-   **전략명**: `bollinger_bands_strategy`
-   **설명**: 주가의 변동성을 측정하는 지표로, 이동평균선을 중심으로 표준편차 범위의 상단/하단 밴드를 형성합니다. 가격이 밴드를 어떻게 터치하는지에 따라 매매 시점을 결정합니다.
-   **주요 파라미터**:
    -   `period` (기본값: `20`): 중심선(이동평균) 계산 기간.
    -   `std_dev` (기본값: `2`): 표준편차 배수.
-   **매매 규칙**:
    -   **매수**: 주가가 하단 밴드 아래로 떨어졌을 때 (과매도 상태로 간주).
    -   **매도**: 주가가 상단 밴드 위로 올라가거나(과매수), 중심선(이동평균선)으로 회귀했을 때.

### 6. MACD (이동평균 수렴-확산)

-   **전략명**: `macd_strategy`
-   **설명**: 두 지수이동평균 간의 관계를 보여주는 추세 추종 모멘텀 지표입니다. MACD 선과 그 이동평균인 시그널 선의 교차를 매매 신호로 사용합니다.
-   **주요 파라미터**:
    -   `fast_period` (기본값: `12`): 단기 EMA 기간.
    -   `slow_period` (기본값: `26`): 장기 EMA 기간.
    -   `signal_period` (기본값: `9`): 시그널 선의 EMA 기간.
-   **매매 규칙**:
    -   **매수**: MACD 선이 시그널 선을 상향 돌파할 때 (강세 전환 신호).
    -   **매도**: MACD 선이 시그널 선을 하향 돌파할 때 (약세 전환 신호).

---

## 신규 전략 추가 방법

새로운 기술적 분석 전략을 시스템에 추가하는 과정은 다음과 같습니다.

1.  **전략 클래스 생성 (`app/strategies/strategies.py`)**
    -   `backtesting.Strategy`와 `PositionSizingMixin`을 상속받는 새로운 클래스를 정의합니다.
    -   `init()` 메서드에서 사용할 지표(Indicator)를 초기화합니다.
    -   `next()` 메서드에서 매수/매도 조건을 정의합니다. `calculate_and_buy()`를 호출하여 포지션 크기를 자동으로 계산하고 매수할 수 있습니다.

    ```python
    # 예시: 새로운 전략 클래스
    class MyNewStrategy(Strategy, PositionSizingMixin):
        my_param = 15  # 전략 파라미터 정의

        def init(self):
            # RSI 지표를 예시로 사용
            self.rsi = self.I(RSI, self.data.Close, self.my_param)
            super().init() # PositionSizingMixin 초기화

        def next(self):
            # 매수 조건: RSI < 30
            if self.rsi < 30:
                if not self.position:
                    self.calculate_and_buy() # 포지션이 없으면 매수

            # 매도 조건: RSI > 70
            elif self.rsi > 70:
                if self.position:
                    self.position.close() # 포지션이 있으면 매도
    ```

2.  **전략 등록 (`app/services/strategy_service.py`)**
    -   `STRATEGY_CLASSES` 딕셔너리에 새 전략 클래스를 추가합니다. 키는 프론트엔드에서 사용할 전략의 고유 이름(문자열)입니다.

    ```python
    STRATEGY_CLASSES = {
        # ... 기존 전략들
        "my_new_strategy": MyNewStrategy,
    }
    ```

3.  **API 스키마 추가 (`app/schemas/requests.py`)**
    -   `StrategyType` 열거형(Enum)에 새로운 전략 이름을 추가하여 API가 해당 전략을 인식할 수 있도록 합니다.

    ```python
    class StrategyType(str, Enum):
        # ... 기존 전략들
        MY_NEW_STRATEGY = "my_new_strategy"
    ```
