package com.search.persistence.repository;

import com.search.persistence.entity.GitRepo;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface GitRepoRepository extends JpaRepository<GitRepo, Long> {
    Optional<GitRepo> findByRepositoryLink(String repositoryLink);
}
