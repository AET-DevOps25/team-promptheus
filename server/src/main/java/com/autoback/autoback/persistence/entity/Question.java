package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.Getter;

import java.time.Instant;
import java.util.List;

@Entity
@Table(name = "questions")
@Getter
public class Question {
    @Id
    @Column(nullable = false)
    private Long id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;
    @Column(nullable = false)
    private String question;
    @Column(name = "created_at",nullable = false)
    private Instant createdAt;

    @OneToMany(mappedBy = "questionId")
    private List<QuestionAnswer> answers;
}