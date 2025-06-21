package com.autoback.autoback.persistence.repository;

import com.autoback.autoback.persistence.entity.Content;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Set;

public interface GitContentRepository extends JpaRepository<Content, String> {
    Set<Content> findDistinctByCreatedAtAfterAndGitRepositoryId(java.time.Instant createdAt, Long gitRepositoryId);
}
