package de.promptheus.contributions.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "git_repositories")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class GitRepository {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "repository_link", nullable = false, length = 255)
    private String repositoryLink;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "last_fetched_at")
    private Instant lastFetchedAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
    }
}
