package com.webproject.backtest_be_spring.domain.user;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

@Converter(autoApply = true)
public class InvestmentTypeConverter implements AttributeConverter<InvestmentType, String> {

    @Override
    public String convertToDatabaseColumn(InvestmentType attribute) {
        return attribute == null ? null : attribute.toDatabaseValue();
    }

    @Override
    public InvestmentType convertToEntityAttribute(String dbData) {
        return dbData == null ? null : InvestmentType.fromDatabaseValue(dbData);
    }
}
