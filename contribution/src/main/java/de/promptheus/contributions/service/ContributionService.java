package de.promptheus.contributions.service;

import de.promptheus.contributions.dto.ContributionDto;
import de.promptheus.contributions.entity.Contribution;
import de.promptheus.contributions.repository.ContributionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class ContributionService {

    private final ContributionRepository contributionRepository;

    public Page<ContributionDto> getAllContributions(Pageable pageable) {
        log.debug("Fetching contributions with pagination: {}", pageable);

        Page<Contribution> contributions = contributionRepository.findAll(pageable);

        return contributions.map(ContributionDto::fromEntity);
    }

    public Page<ContributionDto> getContributionsWithFilters(String contributor, Instant startDate, Instant endDate, Pageable pageable) {
        log.debug("Fetching contributions with filters - contributor: {}, startDate: {}, endDate: {}, pagination: {}",
                contributor, startDate, endDate, pageable);

        Page<Contribution> contributions;

        // Use specific repository methods based on which filters are provided
        if (contributor != null && startDate != null && endDate != null) {
            // All filters provided
            contributions = contributionRepository.findByUsernameAndCreatedAtBetween(contributor, startDate, endDate, pageable);
        } else if (contributor != null) {
            // Only contributor filter
            contributions = contributionRepository.findByUsername(contributor, pageable);
        } else if (startDate != null && endDate != null) {
            // Only date range filter
            contributions = contributionRepository.findByCreatedAtBetween(startDate, endDate, pageable);
        } else {
            // No filters - return all
            contributions = contributionRepository.findAll(pageable);
        }

        log.debug("Found {} contributions matching filters", contributions.getTotalElements());

        return contributions.map(ContributionDto::fromEntity);
    }

    @Transactional
    public int updateContributionSelections(List<ContributionDto> contributionDtos) {
        log.debug("Processing {} contribution selection updates", contributionDtos.size());

        int updatedCount = 0;

        for (ContributionDto dto : contributionDtos) {
            // Find contribution by ID (which is now required and validated)
            Optional<Contribution> existingOpt = contributionRepository.findById(dto.getId());

            if (existingOpt.isPresent()) {
                Contribution existing = existingOpt.get();

                // Only update isSelected field, ignore all other fields
                if (!existing.getIsSelected().equals(dto.getIsSelected())) {
                    log.debug("Updating isSelected for contribution {}: {} -> {}",
                            existing.getId(), existing.getIsSelected(), dto.getIsSelected());

                    existing.setIsSelected(dto.getIsSelected());
                    contributionRepository.save(existing);
                    updatedCount++;
                } else {
                    log.debug("No change needed for contribution {}: isSelected already {}",
                            existing.getId(), existing.getIsSelected());
                }
            } else {
                log.warn("No existing contribution found with ID: {}", dto.getId());
            }
        }

        log.info("Updated isSelected status for {} out of {} contributions", updatedCount, contributionDtos.size());

        return updatedCount;
    }
}
