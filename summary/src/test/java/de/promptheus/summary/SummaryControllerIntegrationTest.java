package de.promptheus.summary;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.Network;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.wait.strategy.Wait;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.time.Duration;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;

@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
@ActiveProfiles("test")
class SummaryControllerIntegrationTest {

    private static final Network network = Network.newNetwork();

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13-alpine")
            .withDatabaseName("promptheus")
            .withUsername("postgres")
            .withPassword("postgres")
            .withNetwork(network)
            .withNetworkAliases("db");

    @Container
    static GenericContainer<?> serverContainer = new GenericContainer<>(DockerImageName.parse("ghcr.io/aet-devops25/promptheus-server:main"))
            .withNetwork(network)
            .withEnv("SPRING_DATASOURCE_URL", "jdbc:postgresql://db:5432/promptheus")
            .withEnv("SPRING_DATASOURCE_USERNAME", "postgres")
            .withEnv("SPRING_DATASOURCE_PASSWORD", "postgres")
            .withEnv("SPRING_JPA_HIBERNATE_DDL_AUTO", "validate")
            .withEnv("SPRING_FLYWAY_ENABLED", "true")
            .withEnv("SPRING_FLYWAY_BASELINE_ON_MIGRATE", "true")
            .withEnv("GENAI_SERVICE_URL", "http://mock-genai:3003")
            .withEnv("SUMMARY_SERVICE_URL", "http://mock-summary:8084")
            .withExposedPorts(8080)
            .waitingFor(Wait.forHttp("/actuator/health")
                    .forPort(8080)
                    .withStartupTimeout(Duration.ofMinutes(2)))
            .dependsOn(postgres);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        // Use the same database as the server for consistency
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);

        // Disable schema validation since server handles migrations
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "none");
        registry.add("spring.flyway.enabled", () -> "false");
        registry.add("spring.jpa.properties.hibernate.dialect", () -> "org.hibernate.dialect.PostgreSQLDialect");
    }

    @BeforeAll
    static void setUp() {
        // Start containers in order: postgres first, then server
        postgres.start();
        serverContainer.start();

        // Give server time to complete migrations and fully initialize
        try {
            Thread.sleep(10000); // 10 seconds to ensure migrations are complete
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    @Autowired
    private MockMvc mockMvc;

    @Test
    void testGetSummaries() throws Exception {
        mockMvc.perform(get("/api/summaries"))
                .andExpect(status().isOk());
    }

    @Test
    void testGenerateBackfillSummaries() throws Exception {
        mockMvc.perform(post("/api/summaries/backfill"))
                .andExpect(status().isOk());
    }

    @Test
    public void testGetSummariesWithPagination() throws Exception {
        // Test pagination functionality
        mockMvc.perform(get("/api/summaries")
                .param("page", "0")
                .param("size", "10")
                .param("sort", "createdAt,desc"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.pageable.pageNumber").value(0))
                .andExpect(jsonPath("$.pageable.pageSize").value(10))
                .andExpect(jsonPath("$.totalElements").exists())
                .andExpect(jsonPath("$.totalPages").exists());
    }

    @Test
    public void testGetSummariesWithFilters() throws Exception {
        // Test filtering functionality
        mockMvc.perform(get("/api/summaries")
                .param("week", "2024-W01")
                .param("username", "testuser")
                .param("repository", "owner/repo"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }

    @Test
    public void testGetSummariesResponseStructure() throws Exception {
        // Test that response has correct pagination structure
        mockMvc.perform(get("/api/summaries"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray())
                .andExpect(jsonPath("$.pageable").exists())
                .andExpect(jsonPath("$.totalElements").exists())
                .andExpect(jsonPath("$.totalPages").exists());
    }



    @Test
    public void testGetSummariesDefaultPagination() throws Exception {
        // Test default pagination values
        mockMvc.perform(get("/api/summaries"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.pageable.pageSize").value(20))
                .andExpect(jsonPath("$.pageable.pageNumber").value(0))
                .andExpect(jsonPath("$.sort.sorted").value(true));
    }
}
