package de.promptheus.summary.persistence;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface GitRepositoryRepository extends JpaRepository<GitRepository, Long> {

    @Query(value = """
        SELECT pat.pat
        FROM personal_access_tokens pat
        JOIN personal_access_tokens_git_repositories patgr ON pat.pat = patgr.personal_access_tokens_pat
        WHERE patgr.git_repositories_id = :repositoryId
        LIMIT 1
        """, nativeQuery = true)
    String findTokenByRepositoryId(@Param("repositoryId") Long repositoryId);

    @Query(value = """
        SELECT DISTINCT c.username
        FROM contributions c
        WHERE c.git_repository_id = :repositoryId
        AND c.is_selected = true
        """, nativeQuery = true)
    List<String> findDistinctUsersByRepositoryId(@Param("repositoryId") Long repositoryId);

    /**
     * Find repository by name, checking both the repository_name field and within the repository_link
     */
    @Query("SELECT gr FROM GitRepository gr WHERE gr.repositoryLink LIKE %:repoName%")
    List<GitRepository> findRepoByName(@Param("repoName") String repoName);

    List<GitRepository> findByRepositoryLink(String repositoryLink);
}
