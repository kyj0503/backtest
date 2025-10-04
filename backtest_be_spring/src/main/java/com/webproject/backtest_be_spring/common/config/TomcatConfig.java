package com.webproject.backtest_be_spring.common.config;

import org.apache.catalina.connector.Connector;
import org.springframework.boot.web.embedded.tomcat.TomcatConnectorCustomizer;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Tomcat 설정을 커스터마이징하여 Docker 컨테이너 이름(언더스코어 포함)을 허용합니다.
 * 개발 환경에서 Vite 프록시가 backtest_be_spring:8080 같은 호스트명을 사용할 때
 * Tomcat의 HTTP 파서가 거부하는 문제를 해결합니다.
 */
@Configuration
public class TomcatConfig {

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> tomcatCustomizer() {
        return factory -> factory.addConnectorCustomizers(new TomcatConnectorCustomizer() {
            @Override
            public void customize(Connector connector) {
                connector.setProperty("relaxedPathChars", "[]|");
                connector.setProperty("relaxedQueryChars", "[]|{}^&#x5c;&#x60;&quot;&lt;&gt;");
                // 언더스코어를 포함한 도메인 이름 허용
                connector.setProperty("allowHostHeaderMismatch", "true");
            }
        });
    }
}
