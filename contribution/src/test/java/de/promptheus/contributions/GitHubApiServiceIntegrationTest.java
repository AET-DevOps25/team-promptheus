package de.promptheus.contributions;

import de.promptheus.contributions.entity.PersonalAccessToken;
import de.promptheus.contributions.repository.PersonalAccessTokenRepository;
import de.promptheus.contributions.service.GitHubApiService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for GitHubApiService
 * These tests make real calls to GitHub API and are disabled by default
 */
@SpringBootTest
@Testcontainers
@ActiveProfiles("test")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@Disabled("Integration tests disabled by default - make real GitHub API calls")
class GitHubApiServiceIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
            .withDatabaseName("test")
            .withUsername("test")
            .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private PersonalAccessTokenRepository patRepository;

    @Autowired
    private ObjectMapper objectMapper;

    private GitHubApiService gitHubApiService;

    private static final String TEST_USER = "WoH";
    private static final String TEST_REPO_URL = "https://github.com/AET-DevOps25/team-promptheus";
    private static final String TEST_GITHUB_TOKEN = "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T";

    @BeforeEach
    void setUp() {
        gitHubApiService = new GitHubApiService(patRepository, objectMapper);

        // Set up test PAT in database
        setupTestPersonalAccessToken();
    }

    @Test
    @Transactional
    void testBasicServiceInitialization() {
        // Test that the service can be initialized properly
        assertNotNull(gitHubApiService, "GitHubApiService should be initialized");
        assertNotNull(patRepository, "PAT repository should be available");
        assertNotNull(objectMapper, "Object mapper should be available");
    }

    private void setupTestPersonalAccessToken() {
        // Clean up existing tokens
        patRepository.deleteAll();

        // Create test PAT
        PersonalAccessToken testPat = new PersonalAccessToken();
        testPat.setPat(TEST_GITHUB_TOKEN);
        testPat.setCreatedAt(Instant.now());

        patRepository.save(testPat);

        System.out.println("Set up test PAT: " + TEST_GITHUB_TOKEN.substring(0, 20) + "...");
    }
}
