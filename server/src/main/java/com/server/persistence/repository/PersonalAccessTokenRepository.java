package com.server.persistence.repository;

import com.server.persistence.entity.PersonalAccessToken;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PersonalAccessTokenRepository extends JpaRepository<PersonalAccessToken, String> {
}
