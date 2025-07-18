package com.server.persistence.repository;

import com.server.persistence.entity.QuestionAnswer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface QuestionAnswerRepository extends JpaRepository<QuestionAnswer, Long> {

    List<QuestionAnswer> findByQuestionIdIn(List<Long> questionIds);

    Optional<QuestionAnswer> findByGenaiQuestionId(String genaiQuestionId);

    List<QuestionAnswer> findByUserNameAndWeekIdOrderByAskedAtDesc(String userName, String weekId);

    List<QuestionAnswer> findByConversationIdOrderByAskedAtAsc(String conversationId);

    List<QuestionAnswer> findByUserNameAndAskedAtAfterOrderByAskedAtDesc(String userName, Instant after);

    @Query(value = """
        SELECT DISTINCT qa.* FROM question_answers qa
        WHERE EXISTS (
            SELECT 1 FROM jsonb_array_elements(qa.full_response->'evidence') AS evidence
            WHERE evidence->>'contribution_id' ILIKE CONCAT('%', :repositoryPattern, '%')
        )
        ORDER BY qa.asked_at DESC
        """, nativeQuery = true)
    List<QuestionAnswer> findByEvidenceFromRepository(@Param("repositoryPattern") String repositoryPattern);
}
