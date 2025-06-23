package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.*;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import com.fasterxml.jackson.databind.JsonNode;

import java.time.Instant;

@Entity
@Table(name = "contributions")
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
    @Column(nullable = false, name = "username")
    private String user;
    @Column(nullable = false)
    private String summary;
    @Column(nullable = false)
    private Boolean isSelected;
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "details", nullable = false)
    @JdbcTypeCode(SqlTypes.JSON)
    private JsonNode details;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
        if (isSelected == null) {
            isSelected = false;
        }
    }
} 
