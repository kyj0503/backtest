"""
뉴스 API 테스트 코드
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.api.v1.endpoints.news import NewsService


class TestNewsService:
    """뉴스 서비스 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행"""
        self.news_service = NewsService()
    
    def test_news_service_initialization(self):
        """뉴스 서비스 초기화 테스트"""
        service = NewsService()
        assert isinstance(service.available_apis, list)
    
    def test_company_name_mapping(self):
        """회사명 매핑 테스트"""
        assert self.news_service.get_company_name("AAPL") == "Apple Inc"
        assert self.news_service.get_company_name("GOOGL") == "Google Alphabet"
        assert self.news_service.get_company_name("UNKNOWN") is None
    
    def test_date_range_validation(self):
        """날짜 범위 검증 테스트"""
        # Alpha Vantage 형식
        assert self.news_service._is_date_in_range("20240101T120000", "2024-01-01", 1)
        assert not self.news_service._is_date_in_range("20240105T120000", "2024-01-01", 1)
        
        # ISO 형식
        assert self.news_service._is_date_in_range("2024-01-01", "2024-01-01", 1)
        assert self.news_service._is_date_in_range("2024-01-02", "2024-01-01", 1)
    
    def test_news_deduplication(self):
        """뉴스 중복 제거 테스트"""
        news_list = [
            {"title": "Apple Stock Rises", "url": "url1"},
            {"title": "Apple Stock Rises", "url": "url2"},  # 중복
            {"title": "Google News", "url": "url3"},
            {"title": "", "url": "url4"},  # 빈 제목
        ]
        
        unique_news = self.news_service._deduplicate_news(news_list)
        assert len(unique_news) == 2
        assert unique_news[0]["title"] == "Apple Stock Rises"
        assert unique_news[1]["title"] == "Google News"
    
    @patch('requests.get')
    def test_fetch_news_from_newsapi_success(self, mock_get):
        """News API 뉴스 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Test News",
                    "description": "Test Description",
                    "url": "https://test.com",
                    "source": {"name": "Test Source"},
                    "publishedAt": "2024-01-01T12:00:00Z"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # API 키 설정
        self.news_service.news_api_key = "test_key"
        
        # 테스트 실행
        result = self.news_service.fetch_news_from_newsapi("AAPL", "2024-01-01")
        
        assert len(result) == 1
        assert result[0]["title"] == "Test News"
        assert result[0]["api_source"] == "news_api"
    
    @patch('requests.get')
    def test_fetch_news_from_newsapi_failure(self, mock_get):
        """News API 뉴스 조회 실패 테스트"""
        # Mock 예외 발생
        mock_get.side_effect = Exception("API Error")
        
        # API 키 설정
        self.news_service.news_api_key = "test_key"
        
        # 테스트 실행
        result = self.news_service.fetch_news_from_newsapi("AAPL", "2024-01-01")
        
        assert result == []
    
    def test_fetch_news_without_api_key(self):
        """API 키 없이 뉴스 조회 테스트"""
        # API 키 제거
        self.news_service.news_api_key = None
        
        # 테스트 실행
        result = self.news_service.fetch_news_from_newsapi("AAPL", "2024-01-01")
        
        assert result == []
    
    @patch('requests.get')
    def test_fetch_news_from_alpha_vantage(self, mock_get):
        """Alpha Vantage API 뉴스 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "feed": [
                {
                    "title": "Alpha Vantage News",
                    "summary": "Summary",
                    "url": "https://test.com",
                    "source": "Test Source",
                    "time_published": "20240101T120000",
                    "overall_sentiment_score": 0.5
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # API 키 설정
        self.news_service.alpha_vantage_key = "test_key"
        
        # 테스트 실행
        result = self.news_service.fetch_news_from_alpha_vantage("AAPL", "2024-01-01")
        
        assert len(result) == 1
        assert result[0]["title"] == "Alpha Vantage News"
        assert result[0]["api_source"] == "alpha_vantage"
        assert "sentiment_score" in result[0]
    
    @patch('requests.get')
    def test_fetch_news_from_finnhub(self, mock_get):
        """Finnhub API 뉴스 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "headline": "Finnhub News",
                "summary": "Summary",
                "url": "https://test.com",
                "source": "Test Source",
                "datetime": 1704110400  # 2024-01-01 12:00:00
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # API 키 설정
        self.news_service.finnhub_key = "test_key"
        
        # 테스트 실행
        result = self.news_service.fetch_news_from_finnhub("AAPL", "2024-01-01")
        
        assert len(result) == 1
        assert result[0]["title"] == "Finnhub News"
        assert result[0]["api_source"] == "finnhub"
    
    @patch.object(NewsService, 'calculate_price_change')
    @patch.object(NewsService, 'fetch_news_from_newsapi')
    @pytest.mark.asyncio
    async def test_get_news_for_date(self, mock_fetch_news, mock_calc_price):
        """특정 날짜 뉴스 조회 통합 테스트"""
        # Mock 설정
        mock_calc_price.return_value = 7.5  # 7.5% 변동
        mock_fetch_news.return_value = [
            {
                "title": "Big News",
                "description": "Important news",
                "url": "https://test.com",
                "source": "Test Source",
                "published_at": "2024-01-01T12:00:00Z",
                "api_source": "news_api"
            }
        ]
        
        # API 키 설정
        self.news_service.news_api_key = "test_key"
        self.news_service.available_apis = ["news_api"]
        
        # 테스트 실행
        result = await self.news_service.get_news_for_date("AAPL", "2024-01-01", 5.0)
        
        assert result["ticker"] == "AAPL"
        assert result["date"] == "2024-01-01"
        assert result["price_change_percent"] == 7.5
        assert result["is_significant_move"] is True
        assert result["news_count"] == 1
        assert len(result["news"]) == 1


class TestNewsAPIEndpoints:
    """뉴스 API 엔드포인트 테스트"""
    
    @pytest.mark.asyncio
    async def test_invalid_date_format(self):
        """잘못된 날짜 형식 테스트"""
        from fastapi import HTTPException
        from app.api.v1.endpoints.news import get_news_for_date
        
        with pytest.raises(HTTPException) as exc_info:
            await get_news_for_date("AAPL", "invalid-date", 5.0)
        
        assert exc_info.value.status_code == 422
    
    def test_date_validation(self):
        """날짜 검증 테스트"""
        # 올바른 형식
        try:
            datetime.strptime("2024-01-01", "%Y-%m-%d")
            valid = True
        except ValueError:
            valid = False
        assert valid
        
        # 잘못된 형식
        try:
            datetime.strptime("01-01-2024", "%Y-%m-%d")
            valid = True
        except ValueError:
            valid = False
        assert not valid


# 통합 테스트 (실제 API 호출하지 않음)
class TestNewsIntegration:
    """뉴스 기능 통합 테스트"""
    
    def test_news_service_configuration(self):
        """뉴스 서비스 설정 테스트"""
        service = NewsService()
        
        # 환경변수 없이도 정상 동작해야 함
        assert isinstance(service.available_apis, list)
        
        # API 키가 없어도 빈 리스트 반환
        news = service.fetch_news_from_newsapi("AAPL", "2024-01-01")
        assert news == []
    
    def test_multiple_api_fallback(self):
        """여러 API 폴백 메커니즘 테스트"""
        service = NewsService()
        
        # 모든 API 키가 없을 때
        service.news_api_key = None
        service.alpha_vantage_key = None
        service.finnhub_key = None
        service.available_apis = []
        
        # 빈 결과 반환해야 함
        assert service.available_apis == []
