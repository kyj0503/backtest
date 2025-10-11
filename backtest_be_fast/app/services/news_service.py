"""
네이버 뉴스 검색 서비스

비즈니스 로직:
- 네이버 검색 API 호출
- HTML 태그 제거 및 텍스트 정리
- 뉴스 관련성 필터링
- 날짜별 뉴스 검색
"""
import logging
import urllib.request
import urllib.parse
import json
import re
import time
import socket
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..core.config import settings

logger = logging.getLogger(__name__)


class NaverNewsService:
    """네이버 검색 API를 사용한 뉴스 서비스"""

    # 티커에 따른 한국어 검색어 매핑
    TICKER_MAPPING = {
        # 미국 주요 종목
        "AAPL": "애플",
        "MSFT": "마이크로소프트",
        "GOOGL": "구글",
        "AMZN": "아마존",
        "TSLA": "테슬라",
        "META": "메타",
        "NVDA": "엔비디아",
        "NFLX": "넷플릭스",
        "AMD": "AMD",
        "INTC": "인텔",
        "CRM": "세일즈포스",
        "ORCL": "오라클",
        "ADBE": "어도비",
        "PYPL": "페이팔",
        "UBER": "우버",
        "SNAP": "스냅챗",
        "SPOT": "스포티파이",
        "SQ": "스퀘어",
        "ZOOM": "줌",
        "SHOP": "쇼피파이",
        "ROKU": "로쿠",
        "PINS": "핀터레스트",
        "DOCU": "도큐사인",
        "OKTA": "옥타",
        "DDOG": "데이터독",
        "SNOW": "스노우플레이크",
        "PLTR": "팔란티어",
        "RBLX": "로블록스",
        "U": "유니티",
        "COIN": "코인베이스",
        "RIVN": "리비안",
        "LCID": "루시드",

        # 한국 주요 종목
        "005930.KS": "삼성전자",
        "000660.KS": "SK하이닉스",
        "035420.KS": "NAVER",
        "207940.KS": "삼성바이오로직스",
        "006400.KS": "삼성SDI",
        "051910.KS": "LG화학",
        "373220.KS": "LG에너지솔루션",
        "000270.KS": "기아",
        "005380.KS": "현대차",
        "035720.KS": "카카오",
        "096770.KS": "SK이노베이션",
        "017670.KS": "SK텔레콤",
        "030200.KS": "KT",
        "055550.KS": "신한지주",
        "105560.KS": "KB금융",
        "086790.KS": "하나금융지주",
        "316140.KS": "우리금융지주",
        "028260.KS": "삼성물산",
        "010950.KS": "S-Oil",
        "009150.KS": "삼성전기",
        "323410.KS": "카카오뱅크",
        "018260.KS": "삼성에스디에스",
        "068270.KS": "셀트리온",
        "003670.KS": "포스코퓨처엠",
        "066570.KS": "LG전자",
        "034730.KS": "SK",
        "015760.KS": "한국전력",
        "036570.KS": "엔씨소프트",
        "012330.KS": "현대모비스",
        "003550.KS": "LG",
        "251270.KS": "넷마블",
        "009540.KS": "HD한국조선해양",
        "032830.KS": "삼성생명",
        "033780.KS": "KT&G",
        "090430.KS": "아모레퍼시픽",
        "180640.KS": "한진칼",
        "128940.KS": "한미약품",
        "047050.KS": "포스코인터내셔널"
    }

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

    def search_news_by_date(self, query: str, start_date: str, end_date: str = None, display: int = 100, sort: str = "date") -> List[Dict[str, Any]]:
        """
        날짜별 네이버 뉴스 검색 (검색 후 날짜 필터링)
        
        Args:
            query: 검색어
            start_date: 검색 시작일 (YYYY-MM-DD)
            end_date: 검색 종료일 (YYYY-MM-DD, 없으면 start_date와 동일)
            display: 검색 결과 수 (필터링 전)
            sort: 정렬 방식 (date, sim)
        """
        max_retries = 3
        retry_delay = 1
        
        # 날짜 범위 설정
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else start_dt
        
        # 종료일을 하루 뒤로 설정 (해당 날짜 전체 포함)
        end_dt = end_dt + timedelta(days=1)
        
        for attempt in range(max_retries):
            try:
                if not self.client_id or not self.client_secret:
                    raise Exception("네이버 API 키가 설정되지 않았습니다.")
                
                # URL 인코딩 (날짜 파라미터 제거)
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
                
                # HTML 태그 제거 및 날짜 필터링
                news_list = []
                for item in result.get('items', []):
                    title = self.remove_html_tags(item['title'])
                    description = self.remove_html_tags(item['description'])
                    
                    # 관련성 필터링
                    if not self.is_relevant_news(title, description):
                        continue
                    
                    # 날짜 필터링
                    try:
                        # pubDate 형식: "Mon, 01 Sep 2025 21:01:00 +0900"
                        pub_date_str = item['pubDate']
                        # RFC 2822 형식 파싱
                        import email.utils
                        pub_timestamp = email.utils.parsedate_tz(pub_date_str)
                        if pub_timestamp:
                            pub_dt = datetime.fromtimestamp(email.utils.mktime_tz(pub_timestamp))
                            
                            # 날짜 범위 확인
                            if start_dt <= pub_dt < end_dt:
                                news_item = {
                                    'title': title,
                                    'link': item['link'],
                                    'description': description,
                                    'pubDate': item['pubDate']
                                }
                                news_list.append(news_item)
                    except Exception as date_error:
                        # 날짜 파싱 오류 시 해당 아이템은 스킵하지만 로그는 남김
                        logger.warning(f"날짜 파싱 오류: {date_error} - {item.get('pubDate', 'N/A')}")
                        continue
                    
                return news_list
                
            except (urllib.error.URLError, socket.gaierror, socket.timeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"날짜별 뉴스 검색 네트워크 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"날짜별 뉴스 검색 네트워크 연결 실패: {str(e)}")
                    raise Exception(f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}")
            except Exception as e:
                logger.error(f"날짜별 네이버 뉴스 검색 오류: {str(e)}")
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
