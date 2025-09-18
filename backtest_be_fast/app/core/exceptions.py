class BacktestError(Exception):
    """백테스트 관련 커스텀 예외 클래스"""
    def __init__(self, message: str, code: str = "BACKTEST_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message) 