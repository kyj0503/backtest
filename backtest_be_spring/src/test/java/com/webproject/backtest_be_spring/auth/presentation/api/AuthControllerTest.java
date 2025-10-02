package com.webproject.backtest_be_spring.auth.presentation.api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.UUID;
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
    @DisplayName("회원 가입은 사용자 정보와 토큰을 반환한다")
    void signUpReturnsCreated() throws Exception {
        String email = uniqueEmail();

        mockMvc.perform(post("/api/v1/auth/signup")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of(
                                "username", "alice",
                                "email", email,
                                "password", "Password!234"))))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.user.username").value("alice"))
                .andExpect(jsonPath("$.user.email").value(email))
                .andExpect(jsonPath("$.tokens.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.tokens.refreshToken").isNotEmpty());
    }

    @Test
    @DisplayName("로그인은 올바른 자격 증명으로 토큰을 발급한다")
    void loginReturnsTokens() throws Exception {
        String email = uniqueEmail();
        signUp("alice", email, "Password!234");

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of(
                                "email", email,
                                "password", "Password!234"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tokens.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.tokens.refreshToken").isNotEmpty());
    }

    @Test
    @DisplayName("잘못된 비밀번호로는 로그인할 수 없다")
    void loginFailsWithWrongPassword() throws Exception {
        String email = uniqueEmail();
        signUp("alice", email, "Password!234");

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of(
                                "email", email,
                                "password", "WrongPassword"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("리프레시 토큰으로 새 액세스 토큰을 발급한다")
    void refreshTokenProvidesNewAccessToken() throws Exception {
        String email = uniqueEmail();
        AuthTokens tokens = signUp("alice", email, "Password!234");

        mockMvc.perform(post("/api/v1/auth/token/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("refreshToken", tokens.refreshToken()))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tokens.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.tokens.refreshToken").isNotEmpty());
    }

    @Test
    @DisplayName("프로필 수정은 인증된 사용자의 정보를 갱신한다")
    void updateProfileWithValidToken() throws Exception {
        String email = uniqueEmail();
        AuthTokens tokens = signUp("alice", email, "Password!234");

        mockMvc.perform(patch("/api/v1/users/me")
                        .header("Authorization", "Bearer " + tokens.accessToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of(
                                "username", "alice-renamed",
                                "investmentType", "balanced"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("alice-renamed"))
                .andExpect(jsonPath("$.email").value(email));
    }

    private AuthTokens signUp(String username, String email, String password) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/v1/auth/signup")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of(
                                "username", username,
                                "email", email,
                                "password", password))))
                .andExpect(status().isCreated())
                .andReturn();

        String responseBody = result.getResponse().getContentAsString();
        String accessToken = objectMapper.readTree(responseBody).path("tokens").path("accessToken").asText();
        String refreshToken = objectMapper.readTree(responseBody).path("tokens").path("refreshToken").asText();
        return new AuthTokens(accessToken, refreshToken);
    }

    private String json(Map<String, ?> values) throws Exception {
        return objectMapper.writeValueAsString(values);
    }

    private String uniqueEmail() {
        return "user" + UUID.randomUUID().toString().substring(0, 8) + "@example.com";
    }

    private record AuthTokens(String accessToken, String refreshToken) {
    }
}
