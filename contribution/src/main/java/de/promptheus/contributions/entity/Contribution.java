package de.promptheus.contributions.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import com.fasterxml.jackson.databind.JsonNode;

import java.time.Instant;

@Entity
@Table(name = "contributions")
@IdClass(ContributionId.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Contribution {

    @Id
    @Column(name = "type", nullable = false, length = 50)
    private String type;

    @Id
    @Column(nullable = false)
    private String id;

    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;

    @Column(name = "username", nullable = false, length = 255)
    private String username;

    @Column(name = "summary", nullable = false)
    private String summary;

    @Column(name = "is_selected", nullable = false)
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
            isSelected = true;  // Database default is true
        }
    }
}
