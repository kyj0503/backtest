package com.webproject.backtest_be_spring.auth.presentation.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("회원 가입과 로그인 API 플로우를 검증한다")
    void signUpLoginAndFetchProfile() throws Exception {
        // 회원 가입
        MvcResult signupResult = mockMvc.perform(post("/api/v1/auth/signup")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{" +
                                "\"username\":\"alice\"," +
                                "\"email\":\"alice@example.com\"," +
                                "\"password\":\"Password!234\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.user.username").value("alice"))
                .andExpect(jsonPath("$.tokens.accessToken").isNotEmpty())
                .andReturn();

        JsonNode signupJson = objectMapper.readTree(signupResult.getResponse().getContentAsString());
        String accessToken = signupJson.path("tokens").path("accessToken").asText();
        String refreshToken = signupJson.path("tokens").path("refreshToken").asText();

        // 로그인
        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{" +
                                "\"email\":\"alice@example.com\"," +
                                "\"password\":\"Password!234\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tokens.accessToken").isNotEmpty());

        // 리프레시 토큰 발급
        MvcResult refreshResult = mockMvc.perform(post("/api/v1/auth/token/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{" +
                                "\"refreshToken\":\"" + refreshToken + "\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tokens.accessToken").isNotEmpty())
                .andReturn();

        String refreshedAccessToken = objectMapper
                .readTree(refreshResult.getResponse().getContentAsString())
                .path("tokens").path("accessToken").asText();

        // 프로필 조회
        mockMvc.perform(get("/api/v1/users/me")
                        .header("Authorization", "Bearer " + refreshedAccessToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("alice"))
                .andExpect(jsonPath("$.email").value("alice@example.com"));

        // 프로필 수정
        mockMvc.perform(patch("/api/v1/users/me")
                        .header("Authorization", "Bearer " + refreshedAccessToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{" +
                                "\"username\":\"alice-renamed\"," +
                                "\"investmentType\":\"balanced\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("alice-renamed"));
    }
}
