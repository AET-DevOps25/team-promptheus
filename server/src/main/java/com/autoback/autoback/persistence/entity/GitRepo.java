package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "git_repositories")
@Getter
@Builder
@AllArgsConstructor
public class GitRepo {
    @Id
    @Column(nullable = false)
    private Long id;
    @Column(unique = true, name = "repository_link", nullable = false)
    private String repositoryLink;
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @ManyToMany
    @JoinTable(
            name = "personal_access_tokens_repositories",
            joinColumns = @JoinColumn(name = "repositories_id"),
            inverseJoinColumns = @JoinColumn(name = "personal_access_tokens_pat"))
    private Set<PersonalAccessToken> patsAllowingAccess;

    @OneToMany(mappedBy = "gitRepositoryId")
    private List<Question> questions;

    @OneToMany(mappedBy = "gitRepositoryId")
    private List<Summary> summaries;

    @OneToMany(mappedBy = "gitRepositoryId")
    private List<Content> contents;

    @OneToMany(mappedBy = "gitRepositoryId")
    private List<Link> links;

    public GitRepo(String repoLink) {
        this.repositoryLink = repoLink;
    }

    public GitRepo() {}
}