package com.autoback.autoback.CommunicationObjects;

import com.autoback.autoback.persistence.entity.Summary;
import lombok.Builder;

import java.time.Instant;

@Builder
public record SummaryConstruct(Long id, String summary, Instant createdAt) {
    public static SummaryConstruct from(Summary s) {
        return SummaryConstruct.builder().summary(s.getSummary()).id(s.getId()).createdAt(s.getCreatedAt()).build();
    }
}
