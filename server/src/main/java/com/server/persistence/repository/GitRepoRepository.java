package com.server.persistence.repository;

import com.server.persistence.entity.GitRepo;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GitRepoRepository extends JpaRepository<GitRepo, Long> {
    GitRepo findByRepositoryLink(String repositoryLink);
}
