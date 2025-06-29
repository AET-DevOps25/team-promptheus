package de.promptheus.summary.persistence;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SummaryRepository extends JpaRepository<Summary, Long> {

    List<Summary> findByWeek(String week);

    List<Summary> findByUsernameAndWeek(String username, String week);

    @Query("SELECT DISTINCT s.username FROM Summary s WHERE s.username IS NOT NULL")
    List<String> findDistinctUsernames();
}
