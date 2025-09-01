"""
뉴스 API 엔드포인트
주식의 급등/급락 시점과 관련된 뉴스를 조회하는 API
"""
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
import os
import requests
import logging
from app.core.custom_exceptions import DataNotFoundError
from app.utils.user_messages import create_user_message

router = APIRouter()
logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        # 뉴스 API 설정 (환경변수에서 가져오기)
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        
        # API 우선순위 설정 (사용 가능한 것부터)
        self.available_apis = []
        if self.news_api_key:
            self.available_apis.append("news_api")
        if self.alpha_vantage_key:
            self.available_apis.append("alpha_vantage")
        if self.finnhub_key:
            self.available_apis.append("finnhub")
    
    def calculate_price_change(self, ticker: str, date: str) -> float:
        """해당 날짜의 주가 변동률 계산"""
        try:
            # 실제 구현에서는 data_fetcher를 사용하여 주가 데이터 조회
            # 여기서는 임시로 0.0 반환 (나중에 실제 로직으로 교체)
            return 0.0
        except Exception as e:
            logger.warning(f"주가 변동률 계산 실패: {e}")
            return 0.0
    
    def fetch_news_from_newsapi(self, ticker: str, date: str, company_name: str = None) -> List[dict]:
        """News API에서 뉴스 조회"""
        if not self.news_api_key:
            return []
        
        try:
            # 검색 키워드 구성 (티커와 회사명)
            query_parts = [ticker]
            if company_name:
                query_parts.append(company_name)
            query = " OR ".join(query_parts)
            
            # 날짜 범위 설정 (해당 날짜 ±1일)
            target_date = datetime.strptime(date, "%Y-%m-%d")
            from_date = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")
            to_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "from": from_date,
                "to": to_date,
                "sortBy": "relevancy",
                "language": "en",
                "pageSize": 10,
                "apiKey": self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for article in data.get("articles", []):
                news_items.append({
                    "title": article.get("title"),
                    "description": article.get("description"),
                    "url": article.get("url"),
                    "source": article.get("source", {}).get("name"),
                    "published_at": article.get("publishedAt"),
                    "api_source": "news_api"
                })
            
            return news_items
            
        except Exception as e:
            logger.error(f"News API 호출 실패: {e}")
            return []
    
    def fetch_news_from_alpha_vantage(self, ticker: str, date: str) -> List[dict]:
        """Alpha Vantage News API에서 뉴스 조회"""
        if not self.alpha_vantage_key:
            return []
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "apikey": self.alpha_vantage_key,
                "limit": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for article in data.get("feed", []):
                # 날짜 필터링 (해당 날짜 ±1일)
                article_date = article.get("time_published", "")
                if self._is_date_in_range(article_date, date):
                    news_items.append({
                        "title": article.get("title"),
                        "description": article.get("summary"),
                        "url": article.get("url"),
                        "source": article.get("source"),
                        "published_at": article_date,
                        "sentiment_score": article.get("overall_sentiment_score"),
                        "api_source": "alpha_vantage"
                    })
            
            return news_items
            
        except Exception as e:
            logger.error(f"Alpha Vantage API 호출 실패: {e}")
            return []
    
    def fetch_news_from_finnhub(self, ticker: str, date: str) -> List[dict]:
        """Finnhub News API에서 뉴스 조회"""
        if not self.finnhub_key:
            return []
        
        try:
            # 날짜 범위 설정 (Unix timestamp)
            target_date = datetime.strptime(date, "%Y-%m-%d")
            from_timestamp = int((target_date - timedelta(days=1)).timestamp())
            to_timestamp = int((target_date + timedelta(days=1)).timestamp())
            
            url = "https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": ticker,
                "from": datetime.fromtimestamp(from_timestamp).strftime("%Y-%m-%d"),
                "to": datetime.fromtimestamp(to_timestamp).strftime("%Y-%m-%d"),
                "token": self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            news_items = []
            for article in data:
                news_items.append({
                    "title": article.get("headline"),
                    "description": article.get("summary"),
                    "url": article.get("url"),
                    "source": article.get("source"),
                    "published_at": datetime.fromtimestamp(article.get("datetime", 0)).isoformat(),
                    "api_source": "finnhub"
                })
            
            return news_items
            
        except Exception as e:
            logger.error(f"Finnhub API 호출 실패: {e}")
            return []
    
    def _is_date_in_range(self, article_date: str, target_date: str, days_range: int = 1) -> bool:
        """기사 날짜가 대상 날짜 범위 내에 있는지 확인"""
        try:
            # Alpha Vantage 날짜 형식: YYYYMMDDTHHMMSS
            if "T" in article_date:
                article_dt = datetime.strptime(article_date[:8], "%Y%m%d")
            else:
                article_dt = datetime.strptime(article_date[:10], "%Y-%m-%d")
            
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            diff = abs((article_dt - target_dt).days)
            
            return diff <= days_range
        except Exception:
            return False
    
    def get_company_name(self, ticker: str) -> Optional[str]:
        """티커로부터 회사명 조회 (간단한 매핑)"""
        # 주요 회사들의 티커-회사명 매핑
        company_mapping = {
            "AAPL": "Apple Inc",
            "GOOGL": "Google Alphabet",
            "MSFT": "Microsoft Corporation",
            "AMZN": "Amazon.com Inc",
            "TSLA": "Tesla Inc",
            "NVDA": "NVIDIA Corporation",
            "META": "Meta Platforms",
            "NFLX": "Netflix Inc"
        }
        return company_mapping.get(ticker.upper())
    
    async def get_news_for_date(self, ticker: str, date: str, threshold: float = 5.0) -> dict:
        """특정 날짜의 뉴스 조회"""
        try:
            # 1. 주가 변동률 계산
            price_change = self.calculate_price_change(ticker, date)
            
            # 2. 급등/급락 여부 확인
            is_significant_move = abs(price_change) >= threshold
            
            # 3. 뉴스 조회 (여러 API 시도)
            all_news = []
            company_name = self.get_company_name(ticker)
            
            for api_name in self.available_apis:
                try:
                    if api_name == "news_api":
                        news = self.fetch_news_from_newsapi(ticker, date, company_name)
                    elif api_name == "alpha_vantage":
                        news = self.fetch_news_from_alpha_vantage(ticker, date)
                    elif api_name == "finnhub":
                        news = self.fetch_news_from_finnhub(ticker, date)
                    else:
                        continue
                    
                    all_news.extend(news)
                    
                    # 충분한 뉴스를 찾았으면 중단
                    if len(all_news) >= 5:
                        break
                        
                except Exception as e:
                    logger.warning(f"{api_name} API 호출 실패: {e}")
                    continue
            
            # 4. 뉴스 중복 제거 및 정렬
            unique_news = self._deduplicate_news(all_news)
            sorted_news = sorted(unique_news, key=lambda x: x.get("published_at", ""), reverse=True)
            
            return {
                "ticker": ticker,
                "date": date,
                "price_change_percent": price_change,
                "is_significant_move": is_significant_move,
                "threshold": threshold,
                "news_count": len(sorted_news),
                "news": sorted_news[:5],  # 최대 5개만 반환
                "available_apis": self.available_apis
            }
            
        except Exception as e:
            logger.error(f"뉴스 조회 실패: {e}")
            raise HTTPException(status_code=500, detail="뉴스 조회 중 오류가 발생했습니다.")
    
    def _deduplicate_news(self, news_list: List[dict]) -> List[dict]:
        """뉴스 중복 제거 (제목 기준)"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news

# NewsService 인스턴스 생성
news_service = NewsService()

@router.get("/news/{ticker}/{date}", summary="특정 날짜 뉴스 조회")
async def get_news_for_date(
    ticker: str,
    date: str,
    threshold: float = Query(5.0, description="급등/급락 기준 (%, 기본값: 5.0)")
):
    """
    특정 티커의 특정 날짜 뉴스를 조회합니다.
    
    Args:
        ticker: 주식 티커 (예: AAPL, GOOGL)
        date: 조회할 날짜 (YYYY-MM-DD 형식)
        threshold: 급등/급락 기준 퍼센트 (기본값: 5.0%)
    
    Returns:
        dict: 뉴스 정보 및 주가 변동률
    """
    try:
        # 날짜 형식 검증
        datetime.strptime(date, "%Y-%m-%d")
        
        # 뉴스 조회
        result = await news_service.get_news_for_date(ticker, date, threshold)
        
        if result["news_count"] == 0:
            return create_user_message(
                "info",
                f"{date} 날짜에 {ticker} 관련 주요 뉴스를 찾을 수 없습니다.",
                result
            )
        
        return create_user_message(
            "success",
            f"{ticker}의 {date} 뉴스 {result['news_count']}건을 조회했습니다.",
            result
        )
        
    except ValueError:
        raise HTTPException(status_code=422, detail="올바른 날짜 형식(YYYY-MM-DD)을 입력해주세요.")
    except Exception as e:
        logger.error(f"뉴스 조회 API 오류: {e}")
        raise HTTPException(status_code=500, detail="뉴스 조회 중 오류가 발생했습니다.")

@router.get("/news/test", summary="뉴스 API 테스트")
async def test_news_apis():
    """뉴스 API 연결 상태를 테스트합니다."""
    try:
        # 테스트용 샘플 조회
        result = await news_service.get_news_for_date("AAPL", "2024-01-01", 5.0)
        
        return {
            "status": "success",
            "available_apis": news_service.available_apis,
            "news_api_key_set": bool(news_service.news_api_key),
            "alpha_vantage_key_set": bool(news_service.alpha_vantage_key),
            "finnhub_key_set": bool(news_service.finnhub_key),
            "test_result": {
                "ticker": result["ticker"],
                "news_count": result["news_count"]
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "available_apis": news_service.available_apis
        }
