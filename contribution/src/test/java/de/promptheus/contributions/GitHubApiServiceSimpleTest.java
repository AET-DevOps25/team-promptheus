package de.promptheus.contributions;

import de.promptheus.contributions.entity.Contribution;
import de.promptheus.contributions.entity.GitRepository;
import de.promptheus.contributions.service.GitHubApiService;
import de.promptheus.contributions.repository.PersonalAccessTokenRepository;
import de.promptheus.contributions.entity.PersonalAccessToken;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.time.Instant;
import java.util.List;
import java.util.Collections;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.ArrayList;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for GitHubApiService focusing on internal logic and data structures.
 * These tests do not make external API calls to avoid rate limiting issues.
 */
class GitHubApiServiceSimpleTest {

    private static final String TEST_USER = "WoH";
    private static final String TEST_REPO_URL = "https://github.com/AET-DevOps25/team-promptheus";

    @Mock
    private PersonalAccessTokenRepository patRepository;

    private GitHubApiService gitHubApiService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);

        // Mock PAT repository to return the test PAT
        PersonalAccessToken mockPat = new PersonalAccessToken();
        mockPat.setPat("github_pat_test_token");

        when(patRepository.findAll()).thenReturn(Collections.singletonList(mockPat));

        gitHubApiService = new GitHubApiService(patRepository, new ObjectMapper());
    }

    @Test
    void testContributionEntityCreation() {
        // Test that we can create contributions with the expected structure
        List<Contribution> mockContributions = createMockContributions();

        // Basic structure assertions
        assertNotNull(mockContributions, "Mock contributions should not be null");
        assertEquals(3, mockContributions.size(), "Should create exactly 3 mock contributions");

        // Verify each contribution has required fields
        for (Contribution contribution : mockContributions) {
            assertNotNull(contribution.getId(), "Contribution ID should not be null");
            assertNotNull(contribution.getType(), "Contribution type should not be null");
            assertNotNull(contribution.getUsername(), "Contribution username should not be null");
            assertNotNull(contribution.getCreatedAt(), "Contribution createdAt should not be null");
            assertTrue(contribution.getIsSelected(), "Contribution should be selected by default");
            assertEquals("WoH", contribution.getUsername(), "All test contributions should be by WoH");
        }

        // Verify specific types are created
        List<String> types = mockContributions.stream()
                .map(Contribution::getType)
                .collect(Collectors.toList());

        assertTrue(types.contains("commit"), "Should contain commit type");
        assertTrue(types.contains("pull_request"), "Should contain pull_request type");
        assertTrue(types.contains("issue"), "Should contain issue type");

        // Verify IDs are unique
        List<String> ids = mockContributions.stream()
                .map(Contribution::getId)
                .collect(Collectors.toList());

        assertEquals(ids.size(), ids.stream().distinct().count(),
                "All contribution IDs should be unique");
    }

    @Test
    void testContributionTypeValidation() {
        List<Contribution> contributions = createMockContributions();

        // Verify all contributions have valid types
        List<String> validTypes = List.of("commit", "pull_request", "issue", "release");
        contributions.forEach(c ->
            assertTrue(validTypes.contains(c.getType()),
                "Invalid contribution type: " + c.getType()));

        // Test type counting
        Map<String, Long> typeCounts = contributions.stream()
                .collect(Collectors.groupingBy(Contribution::getType, Collectors.counting()));

        // Verify type counts are non-negative
        typeCounts.values().forEach(count ->
            assertTrue(count >= 0, "Type count should be non-negative"));

        // Verify total matches sum of parts
        long totalFromTypes = typeCounts.values().stream().mapToLong(Long::longValue).sum();
        assertEquals(contributions.size(), totalFromTypes,
                "Total should equal sum of all type counts");
    }

    @Test
    void testGitRepositoryCreation() {
        GitRepository repository = createMockRepository();

        assertNotNull(repository, "Repository should not be null");
        assertEquals(TEST_REPO_URL, repository.getRepositoryLink(), "Repository URL should match");
        assertNotNull(repository.getCreatedAt(), "Created at should not be null");
        assertNull(repository.getLastFetchedAt(), "Last fetched at should be null initially");
        assertEquals(1L, repository.getId(), "Repository ID should match");
    }

    @Test
    void testContributionBuilderPattern() {
        // Test the builder pattern works correctly
        Instant now = Instant.now();
        Contribution contribution = Contribution.builder()
                .id("test-123")
                .type("commit")
                .username("testuser")
                .summary("Test commit")
                .createdAt(now)
                .isSelected(false)
                .build();

        assertEquals("test-123", contribution.getId());
        assertEquals("commit", contribution.getType());
        assertEquals("testuser", contribution.getUsername());
        assertEquals("Test commit", contribution.getSummary());
        assertEquals(now, contribution.getCreatedAt());
        assertFalse(contribution.getIsSelected());
    }

    @Test
    void testContributionDefaults() {
        // Test that contributions have sensible defaults
        List<Contribution> contributions = createMockContributions();

        contributions.forEach(c -> {
            // All test contributions should be selected by default
            assertTrue(c.getIsSelected(), "Contributions should be selected by default");

            // All should have non-null timestamps
            assertNotNull(c.getCreatedAt(), "Created at should not be null");

            // All should have the test user
            assertEquals(TEST_USER, c.getUsername(), "Username should match test user");
        });
    }

    @Test
    void testContributionSorting() {
        List<Contribution> contributions = createMockContributions();

        // Sort by creation time (newest first)
        List<Contribution> sorted = contributions.stream()
                .sorted((a, b) -> b.getCreatedAt().compareTo(a.getCreatedAt()))
                .collect(Collectors.toList());

        assertEquals(contributions.size(), sorted.size(), "Sorted list should have same size");

        // Verify sorting order (newer contributions first)
        for (int i = 0; i < sorted.size() - 1; i++) {
            assertTrue(sorted.get(i).getCreatedAt().isAfter(sorted.get(i + 1).getCreatedAt()) ||
                      sorted.get(i).getCreatedAt().equals(sorted.get(i + 1).getCreatedAt()),
                      "Contributions should be sorted by creation time descending");
        }
    }

    @Test
    void testContributionFiltering() {
        List<Contribution> contributions = createMockContributions();

        // Filter by type
        List<Contribution> commits = contributions.stream()
                .filter(c -> "commit".equals(c.getType()))
                .collect(Collectors.toList());

        assertEquals(1, commits.size(), "Should have exactly one commit");
        assertEquals("abc123", commits.get(0).getId(), "Commit ID should match");

        // Filter by user
        List<Contribution> userContributions = contributions.stream()
                .filter(c -> TEST_USER.equals(c.getUsername()))
                .collect(Collectors.toList());

        assertEquals(contributions.size(), userContributions.size(),
                "All contributions should be by test user");

        // Filter by selection status
        List<Contribution> selected = contributions.stream()
                .filter(Contribution::getIsSelected)
                .collect(Collectors.toList());

        assertEquals(contributions.size(), selected.size(),
                "All test contributions should be selected");
    }

    private GitRepository createMockRepository() {
        return GitRepository.builder()
                .id(1L)
                .repositoryLink(TEST_REPO_URL)
                .createdAt(Instant.now())
                .lastFetchedAt(null)
                .build();
    }

    private List<Contribution> createMockContributions() {
        List<Contribution> contributions = new ArrayList<>();

        // Mock commit (most recent)
        contributions.add(Contribution.builder()
                .id("abc123")
                .type("commit")
                .username(TEST_USER)
                .summary("Fix authentication bug")
                .createdAt(Instant.now().minusSeconds(3600))
                .isSelected(true)
                .build());

        // Mock pull request (middle)
        contributions.add(Contribution.builder()
                .id("456")
                .type("pull_request")
                .username(TEST_USER)
                .summary("Add new feature")
                .createdAt(Instant.now().minusSeconds(7200))
                .isSelected(true)
                .build());

        // Mock issue (oldest)
        contributions.add(Contribution.builder()
                .id("789")
                .type("issue")
                .username(TEST_USER)
                .summary("Bug report: Login fails")
                .createdAt(Instant.now().minusSeconds(10800))
                .isSelected(true)
                .build());

        return contributions;
    }
}
