package com.autoback.autoback.persistence.repository;

import com.autoback.autoback.persistence.entity.PersonalAccessTokensGitRepository;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PersonalAccessToken2GitRepoRepository extends JpaRepository<PersonalAccessTokensGitRepository, String> {
}
