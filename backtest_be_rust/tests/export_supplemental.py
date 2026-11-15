"""Export reference transforms, independent of Rust, in the Python test image."""
import json
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from app.constants import TICKER_TO_COMPANY_NAME
from app.services.unified_data_service import UnifiedDataService
from app.services.news_service import NewsService

root = Path('/rust')
histories = json.loads((root/'tests/fixtures/histories.json').read_text())
def frame(symbol, start=None, end=None):
    df = pd.DataFrame(histories[symbol]['bars'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').rename(columns=str.title)
    return df
service = UnifiedDataService()
prices = {symbol: frame(symbol) for symbol in ['AAPL', 'MSFT']}
expected = {'stock_data': service.collect_stock_data(list(prices), '2023-01-02', '2023-10-31', prices),
            'volatility_events': service.collect_volatility_events(list(prices), '2023-01-02', '2023-10-31', price_histories=prices)}
with patch('app.services.unified_data_service.data_service.get_ticker_data_sync', side_effect=frame):
    expected['exchange_rates'], expected['exchange_stats'] = service.collect_exchange_data('2023-01-02','2023-10-31')
    expected['sp500_benchmark'], expected['nasdaq_benchmark'] = service.collect_benchmark_data('2023-01-02','2023-10-31')
news = NewsService()
examples = ['<b>애플</b> &amp; 삼성', '주식 <img src=x onerror=alert(1)', '수익 &lt; 10 &amp;amp; 전망', '[역사속 오늘] 주식', '오늘의 날씨와 주가']
expected['news_text'] = [{'input': s, 'clean': news.remove_html_tags(s), 'relevant': news.is_relevant_news(news.remove_html_tags(s), '')} for s in examples]
(root/'tests/fixtures/supplemental.json').write_text(json.dumps(expected,ensure_ascii=False,allow_nan=False),encoding='utf-8')
(root/'src/ticker_names.json').write_text(json.dumps(TICKER_TO_COMPANY_NAME,ensure_ascii=False),encoding='utf-8')
print('Exported supplemental reference and ticker names')
