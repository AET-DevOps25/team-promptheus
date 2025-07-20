package de.promptheus.summary.persistence;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.PagingAndSortingRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SummaryRepository extends JpaRepository<Summary, Long>, PagingAndSortingRepository<Summary, Long> {

    List<Summary> findByWeek(String week);

    List<Summary> findByUsernameAndWeek(String username, String week);

    Optional<Summary> findByUsernameAndWeekAndGitRepositoryId(String username, String week, Long gitRepositoryId);

    @Query("SELECT DISTINCT s.username FROM Summary s WHERE s.username IS NOT NULL")
    List<String> findDistinctUsernames();

    // New paginated query methods with filters
    @Query("SELECT s FROM Summary s JOIN GitRepository gr ON s.gitRepositoryId = gr.id " +
           "WHERE (:week IS NULL OR s.week = :week) " +
           "AND (:username IS NULL OR s.username = :username) " +
           "AND (:repositoryLink IS NULL OR gr.repositoryLink LIKE %:repositoryLink%)")
    Page<Summary> findSummariesWithFilters(
            @Param("week") String week,
            @Param("username") String username,
            @Param("repositoryLink") String repositoryLink,
            Pageable pageable);

    // Alternative method using gitRepositoryId directly
    Page<Summary> findByWeekAndUsernameAndGitRepositoryId(String week, String username, Long gitRepositoryId, Pageable pageable);

    Page<Summary> findByWeekAndUsername(String week, String username, Pageable pageable);

    Page<Summary> findByWeekAndGitRepositoryId(String week, Long gitRepositoryId, Pageable pageable);

    Page<Summary> findByWeek(String week, Pageable pageable);

    Page<Summary> findByUsernameAndGitRepositoryId(String username, Long gitRepositoryId, Pageable pageable);

    Page<Summary> findByUsername(String username, Pageable pageable);

    Page<Summary> findByGitRepositoryId(Long gitRepositoryId, Pageable pageable);
}
