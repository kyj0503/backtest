package com.webproject.backtest_be_spring.domain.user;

public enum InvestmentType {
    CONSERVATIVE,
    MODERATE,
    BALANCED,
    AGGRESSIVE,
    SPECULATIVE;

    public static InvestmentType fromDatabaseValue(String value) {
        if (value == null) {
            return BALANCED;
        }
        return InvestmentType.valueOf(value.toUpperCase());
    }

    public String toDatabaseValue() {
        return name().toLowerCase();
    }
}
