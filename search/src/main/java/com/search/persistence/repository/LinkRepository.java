package com.search.persistence.repository;

import com.search.persistence.entity.Link;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface LinkRepository extends JpaRepository<Link, UUID> {
}
