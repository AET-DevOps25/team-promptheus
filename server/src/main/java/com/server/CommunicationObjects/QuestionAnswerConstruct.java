package com.server.CommunicationObjects;

import com.server.persistence.entity.QuestionAnswer;
import lombok.Builder;

import java.time.Instant;

@Builder
public record QuestionAnswerConstruct(String answer, Instant createdAt) {

    public static QuestionAnswerConstruct from(QuestionAnswer a) {
        return QuestionAnswerConstruct.builder().answer(a.getAnswer()).createdAt(a.getCreatedAt()).build();
    }
}
