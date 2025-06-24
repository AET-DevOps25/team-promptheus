package de.promptheus.contributions.repository;

import de.promptheus.contributions.entity.Contribution;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface ContributionRepository extends JpaRepository<Contribution, String> {

    List<Contribution> findByGitRepositoryId(Long gitRepositoryId);

    List<Contribution> findByGitRepositoryIdAndUsername(Long gitRepositoryId, String username);

    List<Contribution> findByGitRepositoryIdAndType(Long gitRepositoryId, String type);

    List<Contribution> findByGitRepositoryIdAndCreatedAtBetween(
            Long gitRepositoryId, Instant startDate, Instant endDate);

    @Query("SELECT c FROM Contribution c WHERE c.gitRepositoryId = :repositoryId AND c.username = :user AND c.type = :type AND c.summary = :summary")
    Optional<Contribution> findExistingContribution(
            @Param("repositoryId") Long repositoryId,
            @Param("user") String user,
            @Param("type") String type,
            @Param("summary") String summary);

    @Query("SELECT COUNT(c) FROM Contribution c WHERE c.gitRepositoryId = :repositoryId")
    Long countByRepositoryId(@Param("repositoryId") Long repositoryId);

    @Query("SELECT c FROM Contribution c WHERE c.isSelected = true")
    List<Contribution> findSelectedContributions();
} 