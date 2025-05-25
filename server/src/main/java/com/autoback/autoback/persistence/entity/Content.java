package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.Getter;

import java.sql.Time;

@Entity
@Table(name = "contents")
@Getter
public class Content {
    @Id
    @Column(nullable = false)
    private Long id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;
    @Column(nullable = false)
    private String type;
    @Column(nullable = false)
    private String user;
    @Column(nullable = false)
    private String summary;
    @Column(name = "created_at", nullable = false)
    private Time createdAt;
}