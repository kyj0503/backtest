package com.webproject.backtest_be_spring.user.domain.model;

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

    public static InvestmentType fromCode(String code) {
        if (code == null) {
            return BALANCED;
        }
        return InvestmentType.valueOf(code.toUpperCase());
    }

    public String getCode() {
        return name().toLowerCase();
    }
}
