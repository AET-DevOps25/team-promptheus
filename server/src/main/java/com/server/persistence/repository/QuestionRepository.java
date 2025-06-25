package com.server.persistence.repository;

import com.server.persistence.entity.Question;
import org.springframework.data.repository.Repository;

public interface QuestionRepository extends Repository<Question, Long> {
    void save(Question question);
}
