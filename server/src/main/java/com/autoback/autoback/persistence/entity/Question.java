package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.time.Instant;
import java.util.List;

@Entity
@Table(name = "questions")
@Getter
@Builder
@AllArgsConstructor
public class Question {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false, columnDefinition = "BIGINT GENERATED ALWAYS AS IDENTITY")
    private Long id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;
    @Column(nullable = false)
    private String question;
    @Column(name = "created_at",nullable = false)
    private Instant createdAt;

    @OneToMany(mappedBy = "questionId")
    private List<QuestionAnswer> answers;

    public Question() {}
}
