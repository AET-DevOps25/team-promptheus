package de.promptheus.contributions;

import de.promptheus.contributions.entity.PersonalAccessToken;
import de.promptheus.contributions.repository.PersonalAccessTokenRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.Disabled;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureWebMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.time.Instant;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * DISABLED INTEGRATION TEST - Makes real GitHub API calls
 *
 * This test starts the full Spring Boot application which triggers:
 * - Scheduled contribution fetching service
 * - Real GitHub API calls that consume rate limits
 *
 * Disabled by default to prevent rate limit exhaustion during test runs.
 */
@SpringBootTest
@AutoConfigureWebMvc
@Testcontainers
@ActiveProfiles("test")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@Disabled("Integration test disabled - starts full app with GitHub API calls")
class ContributionControllerIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private PersonalAccessTokenRepository patRepository;

    @Autowired
    private ObjectMapper objectMapper;

    // Test data from user request
    private static final String TEST_USER = "WoH";
    private static final String TEST_OWNER = "AET-DevOps25";
    private static final String TEST_REPO = "team-promptheus";
    private static final String TEST_WEEK = "2025-W25";
    private static final String TEST_GITHUB_TOKEN = "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T";

    @BeforeEach
    void setUp() {
        setupTestPersonalAccessToken();
    }

    @Test
    @Transactional
    void testGetUserContributionsForWeek() throws Exception {
        mockMvc.perform(get("/api/contributions/user/{username}/repository/{owner}/{repo}/week/{week}",
                        TEST_USER, TEST_OWNER, TEST_REPO, TEST_WEEK)
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.user").value(TEST_USER))
                .andExpect(jsonPath("$.week").value(TEST_WEEK))
                .andExpect(jsonPath("$.repository").value("https://github.com/" + TEST_OWNER + "/" + TEST_REPO))
                .andExpect(jsonPath("$.total_contributions").exists())
                .andExpect(jsonPath("$.contributions").isArray())
                .andExpect(jsonPath("$.fetched_at").exists());
    }

    @Test
    @Transactional
    void testGetUserContributionsForWeekWithInvalidWeek() throws Exception {
        mockMvc.perform(get("/api/contributions/user/{username}/repository/{owner}/{repo}/week/{week}",
                        TEST_USER, TEST_OWNER, TEST_REPO, "invalid-week")
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error").value("Invalid week format. Expected format: 2025-W25"));
    }

    @Test
    @Transactional
    void testGetUserContributionsForWeekWithInvalidRepository() throws Exception {
        mockMvc.perform(get("/api/contributions/user/{username}/repository/{owner}/{repo}/week/{week}",
                        TEST_USER, "invalid-owner", "invalid-repo", TEST_WEEK)
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk()) // Should return 200 with empty results
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.user").value(TEST_USER))
                .andExpect(jsonPath("$.total_contributions").value(0))
                .andExpect(jsonPath("$.contributions").isEmpty());
    }

    @Test
    @Transactional
    void testGetUserContributionsForWeekWithDifferentWeeks() throws Exception {
        String[] testWeeks = {"2025-W01", "2025-W25", "2025-W52"};

        for (String week : testWeeks) {
            mockMvc.perform(get("/api/contributions/user/{username}/repository/{owner}/{repo}/week/{week}",
                            TEST_USER, TEST_OWNER, TEST_REPO, week)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andDo(print())
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.user").value(TEST_USER))
                    .andExpect(jsonPath("$.week").value(week))
                    .andExpect(jsonPath("$.total_contributions").exists())
                    .andExpect(jsonPath("$.contributions").isArray());
        }
    }

    @Test
    @Transactional
    void testGetUserContributionsResponseStructure() throws Exception {
        mockMvc.perform(get("/api/contributions/user/{username}/repository/{owner}/{repo}/week/{week}",
                        TEST_USER, TEST_OWNER, TEST_REPO, TEST_WEEK)
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.user").exists())
                .andExpect(jsonPath("$.week").exists())
                .andExpect(jsonPath("$.repository").exists())
                .andExpect(jsonPath("$.total_contributions").exists())
                .andExpect(jsonPath("$.contributions").exists())
                .andExpect(jsonPath("$.fetched_at").exists())
                .andExpect(jsonPath("$.user").isString())
                .andExpect(jsonPath("$.week").isString())
                .andExpect(jsonPath("$.repository").isString())
                .andExpect(jsonPath("$.total_contributions").isNumber())
                .andExpect(jsonPath("$.contributions").isArray())
                .andExpect(jsonPath("$.fetched_at").isString());
    }

    @Test
    @Transactional
    void testPerformanceAndTimeout() throws Exception {
        long startTime = System.currentTimeMillis();

        mockMvc.perform(get("/api/contributions/user/{username}/repository/{owner}/{repo}/week/{week}",
                        TEST_USER, TEST_OWNER, TEST_REPO, TEST_WEEK)
                        .contentType(MediaType.APPLICATION_JSON))
                .andDo(print())
                .andExpect(status().isOk());

        long endTime = System.currentTimeMillis();
        long duration = endTime - startTime;

        System.out.println("=== Performance Test ===");
        System.out.println("Request completed in: " + duration + "ms");

        // The request should complete within a reasonable time (30 seconds)
        assertTrue(duration < 30000, "Request should complete within 30 seconds");
    }

    private void setupTestPersonalAccessToken() {
        // Clean up existing tokens
        patRepository.deleteAll();

        // Create test PAT
        PersonalAccessToken testPat = new PersonalAccessToken();
        testPat.setPat(TEST_GITHUB_TOKEN);
        testPat.setCreatedAt(Instant.now());

        patRepository.save(testPat);

        System.out.println("Set up test PAT for controller tests: " + TEST_GITHUB_TOKEN.substring(0, 20) + "...");
    }
}
