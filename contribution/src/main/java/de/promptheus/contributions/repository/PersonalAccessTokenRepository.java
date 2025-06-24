package de.promptheus.contributions.repository;

import de.promptheus.contributions.entity.PersonalAccessToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface PersonalAccessTokenRepository extends JpaRepository<PersonalAccessToken, String> {

    @Query(value = """
        SELECT pat.pat
        FROM personal_access_tokens pat
        JOIN personal_access_tokens_git_repositories patgr ON pat.pat = patgr.personal_access_tokens_pat
        WHERE patgr.git_repositories_id = :repositoryId
        LIMIT 1
        """, nativeQuery = true)
    String findTokenByRepositoryId(@Param("repositoryId") Long repositoryId);
}
