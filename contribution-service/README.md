# Contribution Service

## Overview

The Contribution Service is a Spring Boot application designed to fetch GitHub contributions for users within specific projects and time frames, then format and log them in the same structure expected by the GenAI service. This service acts as a bridge between GitHub's API and the existing system architecture.

## Core Functionality

### Primary Goal
Fetch GitHub contributions for a user in a project within a given time frame (calendar week), using PATs already stored in the database, convert them to the same format the GenAI service uses, and log them for further processing.

## Features

### 1. GitHub Integration
- **GitHub REST API Integration**: Connects to GitHub's REST API v4
- **Database PAT Lookup**: Retrieves Personal Access Tokens from the existing database
- **Rate Limiting**: Implements intelligent rate limiting to respect GitHub API limits
- **Repository Access**: Handles both public and private repository access based on stored PAT permissions

### 2. Contribution Fetching
- **User-Specific Contributions**: Fetch contributions for a specific GitHub user
- **Repository-Specific**: Filter contributions by specific repository
- **Week-Based Filtering**: Query contributions within specific calendar weeks (ISO format: 2024-W21)
- **Contribution Types Supported**: 
  - `commit`: Individual commits
  - `pull_request`: Pull requests (opened, merged, reviewed)
  - `issue`: Issues (created, commented, closed)
  - `release`: Repository releases

### 3. Data Processing & Output
- **Format Conversion**: Convert GitHub API responses to match GenAI service's `ContributionMetadata` format
- **Structured Logging**: Log contributions in JSON format for easy parsing
- **Validation**: Ensure all required fields are present and properly formatted
- **Error Handling**: Graceful handling of API rate limits, authentication failures, and network issues

### 4. API Endpoints

#### Core Endpoints
```
GET /api/contributions/user/{username}/repository/{owner}/{repo}/week/{weekId}
POST /api/trigger
GET /api/contributions/health
GET /api/contributions/metrics
```

### 5. Data Models

#### Input Parameters
- **username**: GitHub username (string)
- **owner**: Repository owner (string)
- **repo**: Repository name (string) 
- **weekId**: ISO week format "2024-W21" (string)

#### Output Format (Aligned with GenAI Service)
```json
{
  "user": "johndoe",
  "week": "2024-W21", 
  "repository": "owner/my-project",
  "contributions": [
    {
      "type": "commit",
      "id": "abc123def456...",
      "selected": true
    },
    {
      "type": "pull_request", 
      "id": "42",
      "selected": true
    },
    {
      "type": "issue",
      "id": "15", 
      "selected": true
    },
    {
      "type": "release",
      "id": "v1.2.0",
      "selected": true
    }
  ]
}
```

#### Contribution Types (Enum)
- `commit`: Individual code commits
- `pull_request`: Pull request activities  
- `issue`: Issue-related activities
- `release`: Repository releases

### 6. Database Integration

#### Uses Existing Schema
The service integrates with the existing database schema:

**Table: `git_repositories`**
```sql
CREATE TABLE git_repositories (
    id bigint PRIMARY KEY NOT NULL,
    repository_link text UNIQUE NOT NULL,
    created_at timestamp NOT NULL DEFAULT now(),
    last_fetched_at timestamp NULL  -- Added in V2 migration for tracking fetch times
);
```

**Table: `personal_access_tokens`**
```sql
CREATE TABLE personal_access_tokens (
    pat text PRIMARY KEY NOT NULL,
    created_at timestamp NOT NULL DEFAULT now()
);
```

**Table: `personal_access_tokens_git_repositories`** (Junction Table)
```sql
CREATE TABLE personal_access_tokens_git_repositories (
    personal_access_tokens_pat text NOT NULL,
    git_repositories_id bigint NOT NULL,
    PRIMARY KEY (personal_access_tokens_pat, git_repositories_id),
    FOREIGN KEY (personal_access_tokens_pat) REFERENCES personal_access_tokens(pat),
    FOREIGN KEY (git_repositories_id) REFERENCES git_repositories(id)
);
```

**Table: `contributions`** (Where contributions will be stored)
```sql
CREATE TABLE contributions (
    id text PRIMARY KEY NOT NULL,
    git_repository_id bigint NOT NULL,
    type text NOT NULL,
    user text NOT NULL,
    summary text NOT NULL,
    details jsonb NOT NULL,
    is_selected boolean NOT NULL DEFAULT true,
    created_at timestamp NOT NULL DEFAULT now(),
    FOREIGN KEY (git_repository_id) REFERENCES git_repositories(id)
);
```

#### PAT Lookup Logic
```java
// Lookup PAT for repository
String repositoryUrl = "https://github.com/" + owner + "/" + repo;
GitRepo gitRepo = gitRepoRepository.findByRepositoryLink(repositoryUrl);

// Get associated PATs via junction table
String sql = """
    SELECT pat.pat 
    FROM personal_access_tokens pat
    JOIN personal_access_tokens_git_repositories patgr 
        ON pat.pat = patgr.personal_access_tokens_pat
    WHERE patgr.git_repositories_id = ?
    LIMIT 1
    """;
String pat = jdbcTemplate.queryForObject(sql, String.class, gitRepo.getId());
```

#### Contribution Entity Mapping
```java
@Entity
@Table(name = "contributions")
public class Contribution {
    @Id
    private String id;              // GitHub contribution ID (text)
    
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;   // FK to git_repositories (bigint)
    
    @Column(nullable = false)
    private String type;            // commit|pull_request|issue|release (text)
    
    @Column(nullable = false)
    private String user;            // GitHub username (text)
    
    @Column(nullable = false)
    private String summary;         // Contribution summary/description (text)
    
    @Type(JsonType.class)
    @Column(name = "details", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> details;  // Full GitHub API response data (jsonb)
    
    @Column(name = "is_selected", nullable = false)
    private Boolean isSelected = true;    // Selection flag (boolean, default: true)
    
    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();  // Timestamp (timestamp, default: now())
}
```

### 7. Configuration

#### Environment Variables
```properties
# GitHub API Configuration
GITHUB_API_URL=https://api.github.com
GITHUB_RATE_LIMIT_ENABLED=true

# Database Configuration (shared with main application)
SPRING_DATASOURCE_URL=${DATABASE_URL}
SPRING_DATASOURCE_USERNAME=${DATABASE_USERNAME} 
SPRING_DATASOURCE_PASSWORD=${DATABASE_PASSWORD}

# Application Configuration
SERVER_PORT=8083
SPRING_APPLICATION_NAME=contribution-service
```

## Architecture

### Technology Stack
- **Framework**: Spring Boot 3.5.3
- **Language**: Java 21
- **Database**: PostgreSQL (shared schema)
- **Migration**: Flyway (uses existing migrations)
- **Build Tool**: Gradle
- **Containerization**: Docker
- **Scheduling**: Spring Scheduler (automatic fetching every 2 minutes)

### External Dependencies
- GitHub REST API v4
- Shared PostgreSQL Database
- Existing schema from main application

### Integration Points
- **Database**: Shares schema with main server application
- **GenAI Service**: Outputs data in compatible format for ingestion
- **PAT Management**: Uses existing PAT storage and validation from database

## API Documentation

### Request/Response Examples

#### Fetch Weekly Contributions
```http
GET /api/contributions/user/johndoe/repository/owner/my-project/week/2024-W21

Response:
{
  "user": "johndoe",
  "week": "2024-W21",
  "repository": "owner/my-project", 
  "total_contributions": 8,
  "contributions": [
    {
      "type": "commit",
      "id": "abc123def456789abcdef123456789abcdef12",
      "selected": true
    },
    {
      "type": "pull_request",
      "id": "42", 
      "selected": true
    },
    {
      "type": "issue",
      "id": "15",
      "selected": true
    }
  ],
  "fetched_at": "2024-03-18T10:30:00Z",
  "github_api_calls_used": 3,
  "rate_limit_remaining": 4997,
  "pat_used": "ghp_****...****"
}
```

#### Manual Trigger - All Repositories
```http
POST /api/contributions/trigger

Response:
{
  "status": "SUCCESS",
  "message": "Contribution fetch completed",
  "triggeredAt": "2024-03-15T14:30:00Z",
  "repositoriesProcessed": 5,
  "contributionsFetched": 47,
  "contributionsUpserted": 45,
  "processedRepositories": [
    "https://github.com/owner/repo1",
    "https://github.com/owner/repo2"
  ],
  "errors": [],
  "processingTimeMs": 3500
}
```

#### Manual Trigger - Specific Repository
```http
POST /api/contributions/trigger/repository
Content-Type: application/json

{
  "repositoryUrl": "https://github.com/owner/repo"
}

Response:
{
  "status": "SUCCESS",
  "message": "Contribution fetch completed for repository",
  "triggeredAt": "2024-03-15T14:30:00Z",
  "repositoriesProcessed": 1,
  "contributionsFetched": 12,
  "contributionsUpserted": 10,
  "processedRepositories": ["https://github.com/owner/repo"],
  "errors": [],
  "processingTimeMs": 850
}
```

#### Health Check
```http
GET /api/contributions/health

Response:
{
  "status": "UP",
  "timestamp": "2024-03-18T10:30:00Z",
  "services": {
    "database": "UP",
    "github_api": "UP"
  },
  "rate_limits": {
    "remaining": 4997,
    "limit": 5000,
    "reset_at": "2024-03-18T11:00:00Z"
  }
}
```

## Implementation Details

### PAT Resolution Flow
1. **Repository Lookup**: Find repository in `git_repositories` table by constructed URL
2. **PAT Retrieval**: Get associated PATs from `personal_access_tokens_git_repositories` junction table
3. **PAT Selection**: Use first available PAT (or implement rotation strategy)
4. **GitHub Authentication**: Use retrieved PAT for GitHub API calls

### GitHub API Integration
- **Endpoints Used**:
  - `/repos/{owner}/{repo}/commits` - Fetch commits
  - `/repos/{owner}/{repo}/pulls` - Fetch pull requests  
  - `/repos/{owner}/{repo}/issues` - Fetch issues
  - `/repos/{owner}/{repo}/releases` - Fetch releases
- **Filtering**: Date-based filtering using `since` parameter based on `last_fetched_at`
- **Pagination**: Handle GitHub API pagination for large result sets
- **Authentication**: Bearer token authentication with database-retrieved PAT
- **Incremental Fetching**: Only fetches contributions since last successful fetch per repository

### Automatic Scheduling
- **Frequency**: Runs every 2 minutes automatically
- **Efficiency**: Uses `last_fetched_at` column to only fetch new contributions since last run
- **Error Handling**: Individual repository failures don't stop processing of other repositories
- **Logging**: Detailed logs for each scheduled run with statistics

### Incremental Fetching Strategy
1. **Initial Fetch**: When `last_fetched_at` is NULL, fetches all available contributions
2. **Subsequent Fetches**: Only fetches contributions created/updated since `last_fetched_at`
3. **Timestamp Update**: Updates `last_fetched_at` only after successful processing
4. **Error Recovery**: Failed repositories retain old `last_fetched_at` for retry on next run

### Week Calculation
- **ISO Week Format**: Accepts weeks in "YYYY-WXX" format (e.g., "2024-W21")
- **Date Range Conversion**: Converts ISO week to start/end dates for GitHub API filtering
- **Timezone Handling**: Uses UTC for consistent date calculations

### Data Transformation
```java
// GitHub API Response -> GenAI Compatible Format + Database Storage
ContributionMetadata transform(GitHubCommit commit) {
    return ContributionMetadata.builder()
        .type(ContributionType.COMMIT)
        .id(commit.getSha())
        .selected(true)
        .build();
}

// Store full GitHub API response in database
Contribution saveContribution(GitHubCommit commit, Long repositoryId) {
    return Contribution.builder()
        .id(commit.getSha())
        .gitRepositoryId(repositoryId)
        .type("commit")
        .user(commit.getAuthor().getLogin())
        .summary(commit.getMessage())
        .details(objectMapper.convertValue(commit, Map.class))  // Store full API response
        .isSelected(true)
        .createdAt(Instant.now())
        .build();
}
```

### Logging Output
All fetched contributions are logged in structured JSON format:
```json
{
  "level": "INFO",
  "timestamp": "2024-03-18T10:30:00Z",
  "logger": "ContributionFetcher",
  "message": "Contributions fetched successfully",
  "data": {
    "user": "johndoe",
    "week": "2024-W21", 
    "repository": "owner/my-project",
    "contributions": [...],
    "pat_used": "ghp_****...****"
  }
}
```

## Development Setup

### Prerequisites
- Java 21
- Docker & Docker Compose
- Access to shared PostgreSQL database
- Existing PATs in database (populated via main application signup flow)

### Local Development
```bash
# Clone the repository
git clone <repository-url>
cd contribution-service

# Set up environment variables
cp .env.example .env
# Edit .env with database credentials (same as main server)

# Run with Docker Compose (uses shared database)
docker-compose up -d

# Or run locally
./gradlew bootRun
```

### Testing
```bash
# Run all tests
./gradlew test

# Run integration tests (requires test database with sample PATs)
./gradlew integrationTest

# Test with real GitHub API (uses PATs from test database)
./gradlew test -Dtest.integration=true
```

## Database Schema

### Shared Tables (from existing schema)

#### Core Tables
- **`git_repositories`**: Repository metadata with unique `repository_link` constraint
- **`personal_access_tokens`**: PAT storage with `pat` as primary key  
- **`personal_access_tokens_git_repositories`**: Many-to-many relationship table
- **`contributions`**: Contribution storage (populated by this service)

#### Supporting Tables
- **`links`**: Access control links (UUID primary key, references `git_repository_id`)
- **`questions`**: User questions (references `git_repository_id`)
- **`summaries`**: Generated summaries (references `git_repository_id`)
- **`question_answers`**: Answers to questions (references `question_id`)
- **`contents`**: Legacy table (may be renamed to `contributions` in migration)

### Sample Data Requirements
For testing and development, the database should contain:
```sql
-- Sample repository (note: id is bigint, not auto-generated)
INSERT INTO git_repositories (id, repository_link, created_at) 
VALUES (1, 'https://github.com/owner/my-project', NOW());

-- Sample PAT (pat is the primary key)
INSERT INTO personal_access_tokens (pat, created_at) 
VALUES ('ghp_validPatToken123', NOW());

-- Link PAT to repository (composite primary key)
INSERT INTO personal_access_tokens_git_repositories (personal_access_tokens_pat, git_repositories_id) 
VALUES ('ghp_validPatToken123', 1);
```

### Key Database Constraints
- **`git_repositories.repository_link`**: UNIQUE constraint ensures no duplicate repositories
- **`personal_access_tokens_git_repositories`**: Composite primary key on both foreign key columns
- **All `created_at` fields**: Default to `now()` timestamp
- **`contributions.is_selected`**: Boolean field with default value `true`
- **`contributions.details`**: JSONB field for storing full GitHub API response data

### Migration Required
This service requires the V2 migration to rename the `contents` table to `contributions` and add the `details` column.

**Migration File**: `src/main/resources/db/migration/V2__rename_contents_to_contributions_add_details.sql`

Key changes in the migration:
- Renames `contents` table to `contributions`
- Adds `details jsonb NOT NULL DEFAULT '{}'` column
- Updates foreign key constraint name from `repo_contents` to `repo_contributions`
- Adds GIN indexes on JSONB fields for better query performance
- Adds composite indexes for common query patterns
- Includes table and column comments for documentation

Note: The migration should be coordinated with the main application to ensure compatibility.

## Monitoring and Observability

### Health Checks
- Database connectivity (shared PostgreSQL)
- GitHub API availability and rate limits
- PAT availability for configured repositories
- Memory and CPU usage

### Metrics
- GitHub API response times
- Rate limit usage and remaining quota
- Contribution fetch success/failure rates
- Processing throughput per week/repository
- PAT usage distribution

### Logging
- Structured JSON logging
- GitHub API interaction logs
- Contribution data output logs
- PAT lookup and usage logs (masked PAT values)
- Error and exception tracking with context

## Security Considerations

### Authentication & Authorization
- PAT retrieval from secure database storage
- Repository access validation via existing PAT-repository mappings
- No PAT exposure in logs (masked output)
- Rate limiting per PAT to prevent abuse

### Data Privacy
- No permanent storage of contribution content
- PAT handling follows existing security practices
- Audit logging for PAT usage (with masked values)
- GDPR compliance for user data processing

## Deployment

### Docker
```dockerfile
FROM openjdk:21-jre-slim
COPY build/libs/contributions-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8083
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

### Docker Compose Integration
```yaml
services:
  contribution-service:
    build: ./contribution-service
    ports:
      - "8083:8083"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/postgres
      - SPRING_DATASOURCE_USERNAME=postgres
      - SPRING_DATASOURCE_PASSWORD=${DB_PASSWORD}
    depends_on:
      - db
      - server  # Depends on main server for PAT setup
```

## Integration with GenAI Service

### Data Flow
1. **PAT Lookup**: Contribution service retrieves PAT from database
2. **Fetch**: Uses PAT to fetch from GitHub API
3. **Transform**: Converts to GenAI-compatible format
4. **Log**: Outputs structured data for ingestion
5. **Ingest**: GenAI service can consume the logged output

### Format Compatibility
The output format matches exactly what the GenAI service expects in its `ContributionsIngestRequest`:
- Same `ContributionMetadata` structure
- Compatible `ContributionType` enum values
- Matching field names and data types

## Future Enhancements

### Planned Features
- PAT rotation and load balancing across multiple PATs
- Batch processing for multiple users/repositories
- Async processing with job queues  
- Webhook integration for real-time updates
- Enhanced filtering options (file types, commit sizes)
- Integration with other Git providers

### Performance Optimizations
- Caching for frequently accessed repositories
- Parallel processing for multiple API calls
- Database connection pooling optimization
- GitHub API response caching
- PAT usage optimization and rotation

## Contributing

### Development Guidelines
- Follow existing project conventions
- Write comprehensive tests
- Use conventional commit messages
- Update documentation for new features

### Code Quality
- Minimum 80% test coverage
- Integration tests with real GitHub API
- Static code analysis
- Security vulnerability scanning

## Support

For issues, feature requests, or questions, please create an issue in the project repository or contact the development team.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 