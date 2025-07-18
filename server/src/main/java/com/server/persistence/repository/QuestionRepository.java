package com.server.persistence.repository;

import com.server.persistence.entity.Question;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QuestionRepository extends JpaRepository<Question, Long> {
    List<Question> findByGitRepositoryId(Long gitRepositoryId);
}
