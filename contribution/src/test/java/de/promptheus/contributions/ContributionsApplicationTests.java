package de.promptheus.contributions;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Disabled;
import org.springframework.boot.test.context.SpringBootTest;

/**
 * DISABLED APPLICATION TEST - Starts full Spring Boot context
 *
 * This test loads the complete application context which triggers:
 * - All Spring Boot auto-configuration
 * - Scheduled services including GitHub API calls
 * - Database connections and migrations
 *
 * Disabled by default to prevent GitHub API rate limit consumption during test runs.
 */
@SpringBootTest
@Disabled("Application test disabled - starts full Spring Boot context with GitHub API calls")
class ContributionsApplicationTests {

	@Test
	void contextLoads() {
	}

}
