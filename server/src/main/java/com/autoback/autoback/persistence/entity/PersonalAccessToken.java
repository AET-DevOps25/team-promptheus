package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.ColumnDefault;

import java.time.Instant;
import java.util.Set;

@Entity
@Table(name = "personal_access_tokens")
@Getter
@Setter
@NoArgsConstructor
public class PersonalAccessToken {
    @Id
    @Column(nullable = false)
    private String pat;

    @ManyToMany
    @JoinTable(
            name = "personal_access_tokens_git_repositories",
            joinColumns = @JoinColumn(name = "personal_access_tokens_pat"),
            inverseJoinColumns = @JoinColumn(name = "git_repositories_id"))
    private Set<GitRepo> relatedGitRepos = Set.of();

    @NotNull
    @ColumnDefault("now()")
    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    public PersonalAccessToken(String pat) {
        this.pat = pat;
    }
}