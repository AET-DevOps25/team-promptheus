package com.server.persistence.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "personal_access_tokens_git_repositories", schema = "public")
@NoArgsConstructor
public class PersonalAccessTokensGitRepository {
    @EmbeddedId
    private PersonalAccessTokensGitRepositoryId id;

    @MapsId("personalAccessTokensPat")
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "personal_access_tokens_pat", nullable = false)
    private PersonalAccessToken personalAccessTokensPat;

    @MapsId("gitRepositoriesId")
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "git_repositories_id", nullable = false)
    private GitRepo gitRepositories;

    public PersonalAccessTokensGitRepository(PersonalAccessToken pat, GitRepo repo) {
        id = new PersonalAccessTokensGitRepositoryId(pat.getPat(), repo.getId());
        personalAccessTokensPat = pat;
        gitRepositories = repo;
    }
}
