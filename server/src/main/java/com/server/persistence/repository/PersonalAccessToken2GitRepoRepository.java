package com.server.persistence.repository;

import com.server.persistence.entity.PersonalAccessTokensGitRepository;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PersonalAccessToken2GitRepoRepository extends JpaRepository<PersonalAccessTokensGitRepository, String> {
}
