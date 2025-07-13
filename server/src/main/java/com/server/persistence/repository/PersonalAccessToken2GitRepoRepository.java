package com.server.persistence.repository;

import com.server.persistence.entity.PersonalAccessTokensGitRepository;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PersonalAccessToken2GitRepoRepository extends JpaRepository<PersonalAccessTokensGitRepository, String> {
    List<PersonalAccessTokensGitRepository> findByGitRepositoriesId(Long gitRepositoriesId);
}
