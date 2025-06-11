package com.autoback.autoback.persistence.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.Hibernate;

import java.io.Serial;
import java.io.Serializable;
import java.util.Objects;

@Getter
@AllArgsConstructor
@Setter
@Embeddable
@NoArgsConstructor
public class PersonalAccessTokensGitRepositoryId implements Serializable {
    @Serial
    private static final long serialVersionUID = 4535832652318016399L;
    @NotNull
    @Column(name = "personal_access_tokens_pat", nullable = false, length = Integer.MAX_VALUE)
    private String personalAccessTokensPat;

    @NotNull
    @Column(name = "git_repositories_id", nullable = false)
    private Long gitRepositoriesId;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || Hibernate.getClass(this) != Hibernate.getClass(o)) return false;
        PersonalAccessTokensGitRepositoryId entity = (PersonalAccessTokensGitRepositoryId) o;
        return Objects.equals(this.gitRepositoriesId, entity.gitRepositoriesId) &&
                Objects.equals(this.personalAccessTokensPat, entity.personalAccessTokensPat);
    }

    @Override
    public int hashCode() {
        return Objects.hash(gitRepositoriesId, personalAccessTokensPat);
    }

}