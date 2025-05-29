package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.Getter;

import java.util.UUID;

@Entity
@Table(name = "links")
@Getter
public class Link {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(nullable = false)
    private UUID id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;
    @Column(name = "is_developer", nullable = false)
    private boolean isDeveloper;

    public Link(GitRepo repo, boolean isDev) {
        gitRepositoryId = repo.getId();
        id = UUID.randomUUID();
        isDeveloper = isDev;
    }
    public Link() {}
}