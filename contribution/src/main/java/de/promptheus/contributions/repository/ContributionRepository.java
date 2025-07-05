package de.promptheus.contributions.repository;

import de.promptheus.contributions.entity.Contribution;
import de.promptheus.contributions.entity.ContributionId;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface ContributionRepository extends JpaRepository<Contribution, ContributionId> {

    List<Contribution> findByGitRepositoryId(Long gitRepositoryId);

    List<Contribution> findByGitRepositoryIdAndUsername(Long gitRepositoryId, String username);

    List<Contribution> findByGitRepositoryIdAndType(Long gitRepositoryId, String type);

    List<Contribution> findByGitRepositoryIdAndCreatedAtBetween(
            Long gitRepositoryId, Instant startDate, Instant endDate);

    // Check if contribution exists by type and id (primary key)
    Optional<Contribution> findByTypeAndId(String type, String id);

    @Query("SELECT COUNT(c) FROM Contribution c WHERE c.gitRepositoryId = :repositoryId")
    Long countByRepositoryId(@Param("repositoryId") Long repositoryId);

    @Query("SELECT c FROM Contribution c WHERE c.isSelected = true")
    List<Contribution> findSelectedContributions();

    // New filtering methods with pagination support
    Page<Contribution> findByUsername(String username, Pageable pageable);

    Page<Contribution> findByCreatedAtBetween(Instant startDate, Instant endDate, Pageable pageable);

    Page<Contribution> findByUsernameAndCreatedAtBetween(String username, Instant startDate, Instant endDate, Pageable pageable);


}
