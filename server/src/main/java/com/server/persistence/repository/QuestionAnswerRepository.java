package com.server.persistence.repository;

import com.server.persistence.entity.QuestionAnswer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface QuestionAnswerRepository extends JpaRepository<QuestionAnswer, Long> {

    Optional<QuestionAnswer> findByQuestionId(Long questionId);

    List<QuestionAnswer> findByQuestionIdIn(List<Long> questionIds);
}
