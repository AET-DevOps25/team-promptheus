package com.autoback.autoback.CommunicationObjects;

import com.autoback.autoback.persistence.entity.Content;
import lombok.Builder;

import java.time.Instant;

@Builder
public record ContentConstruct(String id,String type,String user,String summary,Instant createdAt) {

    public static ContentConstruct from(Content c) {
        return ContentConstruct.builder().type(c.getType()).id(c.getId()).user(c.getUser()).summary(c.getSummary()).createdAt(c.getCreatedAt()).build();
    }
}
