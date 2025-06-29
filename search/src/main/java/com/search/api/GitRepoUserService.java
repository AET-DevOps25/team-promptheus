package com.search.api;

import com.search.persistence.entity.*;
import com.search.persistence.repository.*;
import java.time.DayOfWeek;
import java.time.Instant;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class GitRepoUserService {
  private final GitRepoRepository gitRepoRepository;
  private final LinkRepository linkRepository;

  @Autowired
  public GitRepoUserService(GitRepoRepository gitRepoRepository, LinkRepository linkRepository) {
    this.gitRepoRepository = gitRepoRepository;
    this.linkRepository = linkRepository;
  }

  public void ensureAccessRepositoryOrThrow(UUID accessID, String repository) {
    Optional<Link> link = linkRepository.findById(accessID);
    if (!link.isPresent()) {
      throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No such link exists");
    }
    Optional<GitRepo> repo = gitRepoRepository.findByRepositoryLink(repository);
    if (!repo.isPresent()) {
      throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Repository not found");
    }
    if (link.get().getGitRepositoryId() != repo.get().getId()) {
      throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Access denied");
    }
  }
}
