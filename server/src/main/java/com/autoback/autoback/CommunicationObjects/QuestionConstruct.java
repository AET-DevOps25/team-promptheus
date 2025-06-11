package com.autoback.autoback.CommunicationObjects;

import com.autoback.autoback.persistence.entity.Question;
import lombok.Builder;

import java.time.Instant;
import java.util.List;

@Builder
public record QuestionConstruct(String question,Instant createdAt,List<QuestionAnswerConstruct> answers) {
    public static QuestionConstruct from(Question q) {
        List<QuestionAnswerConstruct> answers = q.getAnswers().stream().map(QuestionAnswerConstruct::from).toList();
        return QuestionConstruct.builder().question(q.getQuestion()).createdAt(q.getCreatedAt()).answers(answers).build();
    }
}
