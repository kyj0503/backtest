"""NewsService.remove_html_tags HTML sanitization 회귀 테스트 (P2-44)

기존 구현은 정규식 `<.*?>`로 태그를 제거했다. 이 패턴은 닫는 '>'를 요구하므로,
닫는 '>'가 없는 미종료 페이로드(예: `<img src=x onerror=alert(1)`, 끝에 '>'
없음)는 태그로 인식되지 않아 그대로 통과한다. 프론트엔드는 이미 이 값을
텍스트로만 렌더링하도록 강화되어 있지만(CLAUDE.md 12번), API 자체의 출력에
마크업 잔재가 남아있어서는 안 된다는 것이 이 항목의 요지다 (defense-in-depth).

수정: html.parser.HTMLParser를 상속해 텍스트 노드만 수집하는 파서로 대체하고,
html.unescape로 엔티티를 디코딩한다. 표준 라이브러리만 사용 - requirements.txt에
bleach 등 HTML sanitizer 의존성이 없고, 이 정도 요구사항(태그 제거 + 엔티티
디코딩)에는 stdlib HTMLParser로 충분하다.
"""
import pytest

from app.services.news_service import NewsService


pytestmark = pytest.mark.unit


@pytest.fixture
def service():
    # NewsService.__init__은 settings에서 네이버 API 키를 읽어 없으면 경고 로그만
    # 남긴다 - 네트워크/DB 호출이 없어 그대로 생성해도 안전하다.
    return NewsService()


class TestUnterminatedTagPayloadIsFullyStripped:
    """오늘의 버그: 닫는 '>'가 없는 페이로드가 그대로 통과한다."""

    def test_unterminated_img_onerror_payload_is_removed(self, service):
        payload = "<img src=x onerror=alert(1)"
        result = service.remove_html_tags(payload)

        assert "<" not in result
        assert "onerror" not in result
        assert result == ""

    def test_unterminated_tag_after_legit_prefix_leaves_no_tag_remnant(self, service):
        payload = "Breaking news<script>alert(1)"
        result = service.remove_html_tags(payload)

        assert "<" not in result
        assert "script" not in result


class TestNestedAndOddTagsAreStripped:
    def test_nested_tags_keep_inner_text_only(self, service):
        result = service.remove_html_tags("<b><i>text</b></i>")
        assert result == "text"

    def test_mismatched_unclosed_tags_keep_text_only(self, service):
        result = service.remove_html_tags("<div><span>hello</div>")
        assert result == "hello"

    def test_mixed_case_script_tag_content_survives_only_as_inert_text(self, service):
        result = service.remove_html_tags("<ScRiPt>alert(1)</sCriPt>tail")
        assert "<" not in result
        assert result == "alert(1)tail"

    def test_well_formed_tag_pair_still_stripped_as_before(self, service):
        """회귀 방지: 기존에도 통과하던(닫는 '>' 있는) 정상 케이스는 계속 동작해야 한다."""
        result = service.remove_html_tags("<b>bold</b> normal")
        assert result == "bold normal"


class TestHtmlEntitiesAreDecoded:
    def test_common_named_entities_are_decoded(self, service):
        result = service.remove_html_tags("&quot;hello&amp;world&#39;")
        assert result == "\"hello&world'"

    def test_hex_numeric_entity_is_decoded(self, service):
        result = service.remove_html_tags("quote&#x27;s")
        assert result == "quote's"


class TestPlainTextPassesThroughUnchanged:
    def test_plain_text_without_markup_is_unchanged(self, service):
        text = "삼성전자 3분기 실적 발표, 시장 예상치 상회"
        assert service.remove_html_tags(text) == text

    def test_empty_string_returns_empty_string(self, service):
        assert service.remove_html_tags("") == ""
