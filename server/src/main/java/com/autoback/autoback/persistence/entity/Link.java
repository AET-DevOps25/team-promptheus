package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

import java.util.UUID;

@Entity
@Table(name = "links")
@Getter
@Setter
public class Link {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(nullable = false)
    private UUID id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;

    @NotNull
    @Column(name = "is_maintainer", nullable = false)
    private Boolean isMaintainer = false;

    public Link(GitRepo repo, boolean isMaint) {
        gitRepositoryId = repo.getId();
        id = UUID.randomUUID();
        isMaintainer = isMaint;
    }
    public Link() {}
}