package com.webproject.backtest_be_spring.common.presentation.test;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Tag(name = "Health", description = "테스트용 헬스 체크 API")
public class TestController {

    @GetMapping("")
    @Operation(summary = "루트 응답", description = "헬스 확인을 위한 단순 텍스트를 반환합니다.")
    public String Hello() {
        return "Hello World 3";
    }
}
