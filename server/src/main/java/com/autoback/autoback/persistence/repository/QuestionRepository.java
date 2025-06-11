package com.autoback.autoback.persistence.repository;

import com.autoback.autoback.persistence.entity.Question;
import org.springframework.data.repository.Repository;

public interface QuestionRepository extends Repository<Question, Long> {
    void save(Question question);
}
