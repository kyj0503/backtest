//! The application's MySQL-only SQLx surface. Keep both crates at the same version.
pub use sqlx_core::connection::Connection;
pub use sqlx_core::{error::Error, query::query, query_scalar::query_scalar, row::Row};
pub use sqlx_mysql::{self as mysql, MySqlPool};
