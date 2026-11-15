use regex::Regex;
use serde_json::{Value, json};
use std::{collections::HashMap, sync::LazyLock};

static NAMES: LazyLock<HashMap<String, String>> =
    LazyLock::new(|| serde_json::from_str(include_str!("ticker_names.json")).unwrap());
static EXCLUDED: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(concat!(
    "(?i)\\[역사속 오늘|\\[오늘의 역사|\\[이날의 역사|\\[역사 속 오늘|\\[오늘 이런 일이|\\[Today in History|",
    "미리보는.*신문|내일 신문|석간.*신문|조간.*신문|부고.*별세|별세.*부고|오늘의 날씨|주요뉴스|뉴스픽|방송프로그램|",
    "TV.*편성|라디오.*편성|오늘.*방송|오늘의.*운세|오늘의.*별자리|오늘의.*혈액형|스포츠.*결과|경기.*결과|",
    "오늘의.*메뉴|오늘의.*퀴즈|이벤트.*당첨|공지사항|보도자료|광고.*안내"
)).unwrap()
});

pub fn query(symbol: &str) -> String {
    let name = NAMES
        .get(symbol)
        .map(String::as_str)
        .unwrap_or_else(|| symbol.strip_suffix(".KS").unwrap_or(symbol));
    format!(
        "{name} {}",
        if symbol.ends_with(".KS") {
            "주가"
        } else {
            "주식"
        }
    )
}
pub fn clean(text: &str) -> String {
    let parsed = scraper::Html::parse_fragment(text);
    html_escape::decode_html_entities(&parsed.root_element().text().collect::<String>())
        .into_owned()
}
pub fn relevant(title: &str, description: &str) -> bool {
    !EXCLUDED.is_match(&format!("{title} {description}"))
}
pub fn normalize(item: &Value) -> Option<Value> {
    let title = clean(item["title"].as_str().unwrap_or(""));
    let description = clean(item["description"].as_str().unwrap_or(""));
    relevant(&title, &description).then(|| json!({"title":title,"description":description,"link":item["link"],"pubDate":item["pubDate"]}))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn news_text_and_queries_match_python() {
        let expected: Value =
            serde_json::from_str(include_str!("../tests/fixtures/supplemental.json")).unwrap();
        for example in expected["news_text"].as_array().unwrap() {
            let cleaned = clean(example["input"].as_str().unwrap());
            assert_eq!(cleaned, example["clean"]);
            assert_eq!(json!(relevant(&cleaned, "")), example["relevant"]);
        }
        assert_eq!(query("AAPL"), "애플 주식");
        assert_eq!(query("005930.KS"), "삼성전자 주가");
        assert_eq!(query("123456.KS"), "123456 주가");
        assert_eq!(query("QQQ"), "QQQ 주식");
    }
}
