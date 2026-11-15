# syntax=docker/dockerfile:1
FROM rust:1.99.0-bookworm@sha256:114c7a4425406451c2866b6aafe69fe29b1b298832db1277d411ac73c82d04d6 AS toolchain
RUN rustup component add rustfmt clippy

FROM toolchain AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY openapi.json ./
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/target \
    cargo build --locked --release && cp target/release/backtest-server /usr/local/bin/backtest-server

FROM builder AS test
COPY tests ./tests
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/target \
    cargo fmt --check && cargo clippy --locked --all-targets -- -D warnings && cargo test --locked

FROM toolchain AS audit
WORKDIR /app
RUN --mount=type=cache,target=/usr/local/cargo/registry cargo install cargo-audit --version 0.23.0 --locked
COPY Cargo.lock ./
RUN cargo audit

FROM toolchain AS development
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY openapi.json ./
EXPOSE 8000
CMD ["cargo", "run", "--locked"]

FROM debian:bookworm-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* && useradd --system --create-home app
WORKDIR /app
COPY --from=builder /usr/local/bin/backtest-server /usr/local/bin/backtest-server
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -fsS http://localhost:8000/health || exit 1
ENTRYPOINT ["/usr/local/bin/backtest-server"]
