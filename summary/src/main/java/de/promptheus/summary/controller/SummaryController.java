package de.promptheus.summary.controller;

import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.service.SummaryService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/summaries")
@RequiredArgsConstructor
public class SummaryController {

    private final SummaryService summaryService;

    @GetMapping
    public List<Summary> getSummaries(@RequestParam Optional<String> week) {
        return summaryService.getSummaries(week);
    }

    @PostMapping("/{username}/{week}")
    public void generateSummary(@PathVariable String username, @PathVariable String week) {
        summaryService.generateSummaryForUser(username, week);
    }
}
