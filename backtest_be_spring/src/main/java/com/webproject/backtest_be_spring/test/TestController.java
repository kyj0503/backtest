package com.webproject.backtest_be_spring.test;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class TestController {

    @GetMapping("")
    public String Hello() {
        return "Hello World 3";
    }
}
