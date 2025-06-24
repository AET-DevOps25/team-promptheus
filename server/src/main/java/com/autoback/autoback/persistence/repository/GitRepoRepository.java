package com.autoback.autoback.persistence.repository;

import com.autoback.autoback.persistence.entity.GitRepo;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GitRepoRepository extends JpaRepository<GitRepo, Long> {
    GitRepo findByRepositoryLink(String repositoryLink);
}
