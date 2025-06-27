package de.promptheus.contributions.repository;

import de.promptheus.contributions.entity.GitRepository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface GitRepositoryRepository extends JpaRepository<GitRepository, Long> {

    GitRepository findByRepositoryLink(String repositoryLink);

    @Query("SELECT gr FROM GitRepository gr WHERE gr.lastFetchedAt IS NULL OR gr.lastFetchedAt < :cutoffTime")
    List<GitRepository> findRepositoriesForFetch(Instant cutoffTime);

    @Query("SELECT gr FROM GitRepository gr")
    List<GitRepository> findRepositoriesForFetch();

    @Query("SELECT gr FROM GitRepository gr WHERE gr.lastFetchedAt IS NULL")
    List<GitRepository> findNeverFetchedRepositories();

    @Query("SELECT gr FROM GitRepository gr WHERE gr.lastFetchedAt < :cutoffTime")
    List<GitRepository> findRepositoriesLastFetchedBefore(Instant cutoffTime);
}
