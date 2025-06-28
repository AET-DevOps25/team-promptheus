package com.server.CommunicationObjects;

import com.server.persistence.entity.Question;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;
import java.util.List;
import lombok.Builder;

@Schema(description = "Question submitted by a user with its answers")
@Builder
public record QuestionConstruct(
    @Schema(
        description = "The question text submitted by the user",
        example = "How does the authentication system work?",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String question,

    @Schema(
        description = "Timestamp when the question was created",
        example = "2023-01-15T16:45:22.789Z",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    Instant createdAt,

    @Schema(description = "List of AI-generated answers to this question", nullable = true) List<QuestionAnswerConstruct> answers
) {
    public static QuestionConstruct from(Question q) {
        List<QuestionAnswerConstruct> answers = q.getAnswers().stream().map(QuestionAnswerConstruct::from).toList();
        return QuestionConstruct.builder().question(q.getQuestion()).createdAt(q.getCreatedAt()).answers(answers).build();
    }
}
