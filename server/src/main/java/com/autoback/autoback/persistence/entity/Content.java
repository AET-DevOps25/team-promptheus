package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;

@Entity
@Table(name = "contents")
@Builder
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class Content {
    @Id
    @Column(nullable = false)
    private String id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;
    @Column(nullable = false)
    private String type;
    @Column(nullable = false)
    private String user;
    @Column(nullable = false)
    private String summary;
    @Column(nullable = false)
    private boolean is_selected;
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
}