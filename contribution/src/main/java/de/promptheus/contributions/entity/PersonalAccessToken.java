package de.promptheus.contributions.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import java.time.Instant;

@Entity
@Table(name = "personal_access_tokens")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PersonalAccessToken {

    @Id
    @Column(name = "pat", nullable = false)
    private String pat;

    @NotNull
    @Column(name = "created_at", nullable = false, columnDefinition = "timestamp DEFAULT CURRENT_TIMESTAMP")
    private Instant createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
    }
}
