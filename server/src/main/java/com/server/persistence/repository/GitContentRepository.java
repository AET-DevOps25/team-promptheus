package com.server.persistence.repository;

import com.server.persistence.entity.Content;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Set;

public interface GitContentRepository extends JpaRepository<Content, String> {
    Set<Content> findDistinctByCreatedAtAfterAndGitRepositoryId(java.time.Instant createdAt, Long gitRepositoryId);
}
