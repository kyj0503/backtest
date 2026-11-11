use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use serde_json::json;

#[derive(Debug, Clone)]
pub struct Error(pub u16, pub String);
pub type Result<T> = std::result::Result<T, Error>;
impl Error {
    pub fn validation(message: impl Into<String>) -> Self {
        Self(422, message.into())
    }
    pub fn unavailable(message: impl Into<String>) -> Self {
        Self(503, message.into())
    }
}
impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.1)
    }
}
impl std::error::Error for Error {}
impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let mut response = (
            StatusCode::from_u16(self.0).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            Json(json!({"detail": self.1})),
        )
            .into_response();
        if self.0 == 429 || self.0 == 503 {
            response.headers_mut().insert(
                "retry-after",
                if self.0 == 429 { "10" } else { "30" }.parse().unwrap(),
            );
        }
        response
    }
}
