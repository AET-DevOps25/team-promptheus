package com.autoback.autoback.persistence.repository;

import com.autoback.autoback.persistence.entity.PersonalAccessToken;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PersonalAccessTokenRepository extends JpaRepository<PersonalAccessToken, String> {
}