package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.Getter;

import java.util.Set;

@Entity
@Table(name = "personal_access_tokens")
@Getter
public class PersonalAccessToken {
    @Id
    @Column(nullable = false)
    private String pat;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;

    @ManyToMany
    @JoinTable(
            name = "personal_access_tokens_repositories",
            joinColumns = @JoinColumn(name = "personal_access_tokens_pat"),
            inverseJoinColumns = @JoinColumn(name = "repositories_id"))
    private Set<GitRepo> relatedGitRepos;

    public PersonalAccessToken(GitRepo repoEntity, String pat) {
        gitRepositoryId = repoEntity.getId();
        this.pat = pat;
    }

    public PersonalAccessToken() {}
}