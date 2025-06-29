package com.search.persistence.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "git_repositories")
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class GitRepo {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(nullable = false, columnDefinition = "BIGINT GENERATED ALWAYS AS IDENTITY")
    private Long id;

    @Column(unique = true, name = "repository_link", nullable = false)
    @NotNull
    @NotBlank
    private String repositoryLink;

    @OneToMany(mappedBy = "gitRepositoryId")
    @Builder.Default
    private List<Link> links=List.of();
}
