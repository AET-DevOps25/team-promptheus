package com.autoback.autoback.persistence.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "links")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Link {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(nullable = false)

    private UUID id;
    @Column(name = "git_repository_id", nullable = false)
    private Long gitRepositoryId;

    @NotNull
    @Column(name = "is_maintainer", nullable = false)
    @Builder.Default
    private Boolean isMaintainer = false;

}