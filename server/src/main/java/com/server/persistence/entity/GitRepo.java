package com.server.persistence.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "git_repositories")
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class GitRepo {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false, columnDefinition = "BIGINT GENERATED ALWAYS AS IDENTITY")
    private Long id;

    @Column(unique = true, name = "repository_link", nullable = false)
    @NotNull
    @NotBlank
    private String repositoryLink;

    @Column(name = "created_at", nullable = false)
    @Builder.Default
    private Instant createdAt = Instant.now();

    @ManyToMany
    @JoinTable(
            name = "personal_access_tokens_git_repositories",
            joinColumns = @JoinColumn(name = "git_repositories_id"),
            inverseJoinColumns = @JoinColumn(name = "personal_access_tokens_pat"))
    @Builder.Default
    private Set<PersonalAccessToken> patsAllowingAccess = new LinkedHashSet<>();

    @OneToMany(mappedBy = "gitRepositoryId")
    @Builder.Default
    private List<Question> questions=List.of();

    @OneToMany(mappedBy = "gitRepositoryId")
    @Builder.Default
    private List<Summary> summaries=List.of();

    @OneToMany(mappedBy = "gitRepositoryId")
    @Builder.Default
    private List<Content> contents=List.of();

    @OneToMany(mappedBy = "gitRepositoryId")
    @Builder.Default
    private List<Link> links=List.of();

    @ManyToMany
    @JoinTable(name = "personal_access_tokens_git_repositories",
            joinColumns = @JoinColumn(name = "git_repositories_id"),
            inverseJoinColumns = @JoinColumn(name = "personal_access_tokens_pat"))
    @Builder.Default
    private Set<PersonalAccessToken> personalAccessTokens = new LinkedHashSet<>();

}
