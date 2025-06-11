package com.autoback.autoback.CommunicationObjects;

import com.autoback.autoback.persistence.entity.QuestionAnswer;
import lombok.Builder;

import java.time.Instant;

@Builder
public record QuestionAnswerConstruct(String answer, Instant createdAt) {

    public static QuestionAnswerConstruct from(QuestionAnswer a) {
        return QuestionAnswerConstruct.builder().answer(a.getAnswer()).createdAt(a.getCreatedAt()).build();
    }
}
