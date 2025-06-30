package de.promptheus.summary.persistence;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;

@Entity
@Table(name = "summaries")
@Data
public class Summary {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "git_repository_id")
    private Long gitRepositoryId;

    private String username;

    private String week;

    private String summary;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
