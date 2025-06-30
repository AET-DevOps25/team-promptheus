package de.promptheus.summary.persistence;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.Instant;

@Entity
@Table(name = "git_repositories")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class GitRepository {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "repository_link", nullable = false, unique = true)
    private String repositoryLink;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
}
