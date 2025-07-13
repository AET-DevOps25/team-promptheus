package com.server.persistence.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;

@Entity
@Table(name = "question_answers")
@Getter
@Builder
@AllArgsConstructor
public class QuestionAnswer {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false, columnDefinition = "BIGINT GENERATED ALWAYS AS IDENTITY")
    private Long id;

    @Column(name = "question_id", nullable = false)
    private Long questionId;

    @Column(nullable = false)
    private String answer;

    @Column(name = "confidence")
    private Float confidence;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    // New fields for rich GenAI response data
    @Column(name = "genai_question_id", length = 36)
    private String genaiQuestionId;

    @Column(name = "user_name", length = 100)
    private String userName;

    @Column(name = "week_id", length = 10)
    private String weekId;

    @Column(name = "question_text")
    private String questionText;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "full_response", columnDefinition = "jsonb")
    private String fullResponse;

    @Column(name = "asked_at")
    private Instant askedAt;

    @Column(name = "response_time_ms")
    private Integer responseTimeMs;

    @Column(name = "conversation_id", length = 100)
    private String conversationId;

    public QuestionAnswer() {}

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = Instant.now();
        }
    }
}
