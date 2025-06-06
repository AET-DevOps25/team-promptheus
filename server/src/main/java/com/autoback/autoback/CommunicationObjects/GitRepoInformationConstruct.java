package com.autoback.autoback.CommunicationObjects;

import lombok.Builder;

import java.time.Instant;
import java.util.List;

@Builder
public record GitRepoInformationConstruct(String repoLink, boolean isDeveloper, Instant createdAt,
                                          List<QuestionConstruct> questions, List<SummaryConstruct> summaries,
                                          List<ContentConstruct> contents) {
}
