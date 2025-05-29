package com.autoback.autoback.persistence.repository;

import com.autoback.autoback.persistence.entity.Link;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface LinkRepository extends JpaRepository<Link, UUID> {
}