package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import lombok.Getter;

import java.time.Instant;

@Entity
@Table(name = "question_answers")
@Getter
public class QuestionAnswer {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(nullable = false)
    private Long id;
    @Column(name = "question_id",nullable = false)
    private Long questionId;
    @Column(nullable = false)
    private String answer;
    @Column(name = "created_at",nullable = false)
    private Instant createdAt;
}