"""
뉴스 검색 서비스

**역할**:
- 네이버 검색 API를 사용하여 종목 관련 뉴스 수집
- HTML 태그 제거 및 텍스트 정리
- 뉴스 관련성 필터링 및 날짜별 검색

**주요 기능**:
1. search_news(): 특정 종목의 최신 뉴스 검색
   - 네이버 검색 API 호출
   - HTML 태그 제거 (<b>, &quot; 등)
   - 뉴스 메타데이터 파싱 (제목, 링크, 설명, 날짜)
2. 뉴스 필터링: 관련성 낮은 뉴스 제외
3. 날짜별 검색: 특정 기간의 뉴스만 조회

**API 설정**:
- 네이버 검색 API 키: 환경 변수 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
- 요청 제한: 분당 100건, 일일 25,000건

**의존성**:
- app/repositories/news_repository.py: DB에 뉴스 저장 (선택적)
- app/core/config.py: API 키 설정

**연관 컴포넌트**:
- Backend: app/services/unified_data_service.py (뉴스 수집 호출)
- Backend: app/api/v1/endpoints/backtest.py (뉴스 데이터 응답)
- Frontend: src/features/backtest/components/NewsSection.tsx (뉴스 표시)

**외부 API**:
- Naver Search API: https://developers.naver.com/docs/serviceapi/search/news/news.md
"""
import logging
import urllib.request
import urllib.parse
import json
import re
import time
import socket
from typing import List, Dict, Any
from datetime import datetime

from ..core.config import settings
from ..constants import TICKER_TO_COMPANY_NAME

logger = logging.getLogger(__name__)


class NaverNewsService:
    """네이버 검색 API를 사용한 뉴스 서비스"""

    # 티커 매핑을 외부 상수에서 가져옴
    TICKER_MAPPING = TICKER_TO_COMPANY_NAME

    def __init__(self):
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret

        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 키가 설정되지 않았습니다.")

    def remove_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def is_relevant_news(self, title: str, description: str) -> bool:
        """뉴스의 관련성 판단 - 불필요한 뉴스 필터링"""
        # 제외할 키워드 패턴 (더 강화된 필터링)
        exclude_patterns = [
            r'\[역사속 오늘',  # [역사속 오늘·9.2] 등을 포착
            r'\[오늘의 역사',
            r'\[이날의 역사',
            r'\[역사 속 오늘',
            r'\[오늘 이런 일이',
            r'\[Today in History',
            r'미리보는.*신문',
            r'내일 신문',
            r'석간.*신문',
            r'조간.*신문',
            r'부고.*별세',
            r'별세.*부고',
            r'오늘의 날씨',
            r'주요뉴스',
            r'뉴스픽',
            r'방송프로그램',
            r'TV.*편성',
            r'라디오.*편성',
            r'오늘.*방송',
            r'오늘의.*운세',
            r'오늘의.*별자리',
            r'오늘의.*혈액형',
            r'스포츠.*결과',
            r'경기.*결과',
            r'오늘의.*메뉴',
            r'오늘의.*퀴즈',
            r'이벤트.*당첨',
            r'공지사항',
            r'보도자료',
            r'광고.*안내'
        ]
        
        # 제목과 설명 모두에서 제외 패턴 확인
        text_to_check = f"{title} {description}"
        for pattern in exclude_patterns:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                return False
        
        return True
    
    def search_news(self, query: str, display: int = 10, sort: str = "date") -> List[Dict[str, Any]]:
        """네이버 뉴스 검색 (재시도 로직 포함)"""
        max_retries = 3
        retry_delay = 1  # 초기 대기 시간 (초)
        
        for attempt in range(max_retries):
            try:
                if not self.client_id or not self.client_secret:
                    raise Exception("네이버 API 키가 설정되지 않았습니다.")
                
                # URL 인코딩
                encText = urllib.parse.quote(query)
                url = f"https://openapi.naver.com/v1/search/news?query={encText}&display={display}&sort={sort}"
                
                # API 요청 (타임아웃 10초)
                request = urllib.request.Request(url)
                request.add_header("X-Naver-Client-Id", self.client_id)
                request.add_header("X-Naver-Client-Secret", self.client_secret)
                
                response = urllib.request.urlopen(request, timeout=10)
                response_body = response.read()
                
                # JSON 파싱
                result = json.loads(response_body.decode('utf-8'))
                
                # HTML 태그 제거 및 데이터 정리
                news_list = []
                for item in result.get('items', []):
                    title = self.remove_html_tags(item['title'])
                    description = self.remove_html_tags(item['description'])
                    
                    # 관련성 필터링
                    if not self.is_relevant_news(title, description):
                        continue
                    
                    news_item = {
                        'title': title,
                        'link': item['link'],
                        'description': description,
                        'pubDate': item['pubDate']
                    }
                    news_list.append(news_item)
                    
                return news_list
                
            except (urllib.error.URLError, socket.gaierror, socket.timeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"네트워크 오류 발생 (시도 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                    continue
                else:
                    logger.error(f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}")
                    raise Exception(f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}")
            except Exception as e:
                logger.error(f"네이버 뉴스 검색 오류: {str(e)}")
                raise

    def get_ticker_query(self, ticker: str) -> str:
        """
        종목 코드로부터 검색어 생성
        
        Args:
            ticker: 종목 코드 (예: 005930.KS, AAPL)
        
        Returns:
            str: 검색어 (예: "삼성전자 주가", "애플 주식")
        """
        # 검색어 결정 (회사명으로 정확한 검색)
        if ticker in self.TICKER_MAPPING:
            company_name = self.TICKER_MAPPING[ticker]
            # 한국 기업은 "회사명 주가"로 검색
            if ticker.endswith('.KS'):
                return f"{company_name} 주가"
            else:
                # 해외 기업은 "회사명 주식"으로 검색
                return f"{company_name} 주식"
        else:
            # 매핑에 없는 경우 기본 검색어
            if ticker.endswith('.KS'):
                # 한국 종목의 경우 종목코드를 제거하고 주가 추가
                clean_ticker = ticker.replace('.KS', '')
                return f"{clean_ticker} 주가"
            else:
                # 해외 종목의 경우 티커 그대로 사용
                return f"{ticker} 주식"


# 서비스 인스턴스 (싱글톤)
news_service = NaverNewsService()
