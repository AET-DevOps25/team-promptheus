package com.server.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.server.genai.api.DefaultApi;
import com.server.genai.model.QuestionRequest;
import com.server.genai.model.QuestionResponse;
import com.server.genai.model.QuestionContext;
import com.server.genai.model.ReasoningDepth;
import com.server.summary.api.SummaryControllerApi;
import com.server.summary.model.SummaryDto;
import com.server.summary.model.PageSummaryDto;
import com.server.summary.model.Pageable;
import com.server.persistence.entity.*;
import com.server.persistence.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.time.LocalDate;
import java.time.temporal.WeekFields;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

@Service
public class QuestionAnswerService {

    private static final Logger logger = LoggerFactory.getLogger(QuestionAnswerService.class);

    private final DefaultApi genaiApi;
    private final SummaryControllerApi summaryApi;
    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final GitRepoRepository gitRepoRepository;
    private final PersonalAccessToken2GitRepoRepository pat2gitRepository;

    @Autowired
    public QuestionAnswerService(
            DefaultApi genaiApi,
            SummaryControllerApi summaryApi,
            QuestionRepository questionRepository,
            QuestionAnswerRepository questionAnswerRepository,
            GitRepoRepository gitRepoRepository,
            PersonalAccessToken2GitRepoRepository pat2gitRepository
    ) {
        this.genaiApi = genaiApi;
        this.summaryApi = summaryApi;
        this.questionRepository = questionRepository;
        this.questionAnswerRepository = questionAnswerRepository;
        this.gitRepoRepository = gitRepoRepository;
        this.pat2gitRepository = pat2gitRepository;
    }

    @Async
    public CompletableFuture<Void> processQuestionAsync(Long questionId, String repositoryUrl, String username, String weekId) {
        try {
            Question question = questionRepository.findById(questionId)
                    .orElseThrow(() -> new RuntimeException("Question not found: " + questionId));

            logger.info("Processing question {} for user {} week {} repository {}",
                       questionId, username, weekId, repositoryUrl);

            // Extract repository information from URL
            String[] urlParts = repositoryUrl.replace("https://github.com/", "").split("/");
            if (urlParts.length < 2) {
                throw new RuntimeException("Invalid repository URL format: " + repositoryUrl);
            }
            String owner = urlParts[0];
            String repo = urlParts[1];

            // Get the GitRepo entity to find the PAT
            GitRepo gitRepo = gitRepoRepository.findByRepositoryLink(repositoryUrl);
            if (gitRepo == null) {
                throw new RuntimeException("Repository not found in database: " + repositoryUrl);
            }

            // Get the PAT for this repository
            String githubPat = getPatForRepository(gitRepo.getId());
            if (githubPat == null || githubPat.trim().isEmpty()) {
                throw new RuntimeException("No valid GitHub PAT found for repository: " + repositoryUrl);
            }

            // Get existing Q&A context from the database
            List<QuestionAnswer> previousAnswers = getPreviousAnswersForRepository(gitRepo.getId());

            // Try to get summary from summary service (may 404, that's OK)
            String summaryContext = getSummaryForUserWeek(owner, repo, username, weekId);

            // Build previous Q&A context string
            String previousQAContext = buildPreviousQAContext(previousAnswers);

            // Combine summary and previous context
            String combinedSummary = buildCombinedSummary(summaryContext, previousQAContext);

            // Create context for the question
            QuestionContext questionContext = new QuestionContext()
                    .includeEvidence(true)
                    .reasoningDepth(ReasoningDepth.DETAILED)
                    .maxEvidenceItems(10)
                    .focusAreas(new ArrayList<>());

            // Convert repository URL to owner/repo format for GenAI service
            String repositoryFormat = owner + "/" + repo;

            // Create question request for GenAI
            QuestionRequest questionRequest = new QuestionRequest()
                    .question(question.getQuestion())
                    .repository(repositoryFormat)
                    .summary(combinedSummary)
                    .context(questionContext)
                    .githubPat(githubPat);

            // Call GenAI service
            logger.info("Calling GenAI service for user {} week {} with question: {}",
                       username, weekId, question.getQuestion());

            Mono<QuestionResponse> responseMono = genaiApi
                    .askQuestionAboutUserContributionsUsersUsernameWeeksWeekIdQuestionsPost(
                            username, weekId, questionRequest);

            QuestionResponse response = responseMono.block();

            if (response != null) {
                // Serialize the full response to JSON
                String fullResponseJson;
                try {
                    ObjectMapper objectMapper = new ObjectMapper();
                    objectMapper.registerModule(new JavaTimeModule());
                    fullResponseJson = objectMapper.writeValueAsString(response);
                } catch (JsonProcessingException e) {
                    logger.warn("Failed to serialize GenAI response to JSON for question {}: {}",
                               questionId, e.getMessage());
                    fullResponseJson = null;
                }

                // Convert OffsetDateTime to Instant
                Instant askedAtInstant = null;
                if (response.getAskedAt() != null) {
                    askedAtInstant = response.getAskedAt().toInstant();
                }

                // Save the enhanced answer with full response data
                QuestionAnswer answer = QuestionAnswer.builder()
                        .questionId(questionId)
                        .answer(response.getAnswer())
                        .confidence(response.getConfidence() != null ?
                                response.getConfidence().floatValue() : null)
                        // New rich data fields
                        .genaiQuestionId(response.getQuestionId())
                        .userName(response.getUser())
                        .weekId(response.getWeek())
                        .questionText(response.getQuestion())
                        .fullResponse(fullResponseJson)
                        .askedAt(askedAtInstant)
                        .responseTimeMs(response.getResponseTimeMs())
                        .conversationId(response.getConversationId())
                        .build();

                questionAnswerRepository.save(answer);
                logger.info("Successfully processed question {} with enhanced answer data for user {} week {}",
                           questionId, username, weekId);
            } else {
                logger.warn("No response received from GenAI service for question {}", questionId);
            }

        } catch (Exception e) {
            logger.error("Error processing question {}: {}", questionId, e.getMessage(), e);

            // Save error response
            QuestionAnswer errorAnswer = QuestionAnswer.builder()
                    .questionId(questionId)
                    .answer("Error processing question: " + e.getMessage())
                    // .confidence(0.0f)  // TODO: Uncomment after migration V8
                    .build();

            questionAnswerRepository.save(errorAnswer);
        }

        return CompletableFuture.completedFuture(null);
    }

    private String getPatForRepository(Long gitRepoId) {
        // Find the PAT associated with this repository
        List<PersonalAccessTokensGitRepository> patRepoLinks = pat2gitRepository.findByGitRepositoriesId(gitRepoId);
        if (patRepoLinks.isEmpty()) {
            logger.warn("No PAT found for repository ID: {}", gitRepoId);
            return null;
        }

        // Return the first PAT found
        return patRepoLinks.get(0).getPersonalAccessTokensPat().getPat();
    }

    private List<QuestionAnswer> getPreviousAnswersForRepository(Long gitRepoId) {
        // Get all questions for this repository
        List<Question> questions = questionRepository.findByGitRepositoryId(gitRepoId);
        List<Long> questionIds = questions.stream().map(Question::getId).toList();

        // Get all answers for these questions
        return questionAnswerRepository.findByQuestionIdIn(questionIds);
    }

    private String getSummaryForUserWeek(String owner, String repo, String username, String weekId) {
        try {
            logger.info("Fetching summary for {}/{} user {} week {}", owner, repo, username, weekId);

            // Use the generated client to fetch summaries with proper parameters
            Pageable pageable = new Pageable()
                    .page(0)
                    .size(20)
                    .addSortItem("createdAt,desc");

            String repositoryFilter = owner + "/" + repo;

            PageSummaryDto page = summaryApi.getSummaries(pageable, weekId, username, repositoryFilter)
                    .block();

            if (page == null || page.getContent() == null || page.getContent().isEmpty()) {
                logger.warn("No summaries found for user {} week {} repository {}", username, weekId, repositoryFilter);
                return null;
            }

            // Get the first summary (should be filtered by username already)
            SummaryDto summary = page.getContent().get(0);
            logger.info("Found summary for user {} week {}", username, weekId);

            // Build a comprehensive summary context from all available fields
            StringBuilder summaryContext = new StringBuilder();
            if (summary.getOverview() != null) {
                summaryContext.append("Overview: ").append(summary.getOverview()).append("\n");
            }
            if (summary.getAnalysis() != null) {
                summaryContext.append("Analysis: ").append(summary.getAnalysis()).append("\n");
            }
            if (summary.getCommitsSummary() != null) {
                summaryContext.append("Commits: ").append(summary.getCommitsSummary()).append("\n");
            }
            if (summary.getPullRequestsSummary() != null) {
                summaryContext.append("Pull Requests: ").append(summary.getPullRequestsSummary()).append("\n");
            }
            if (summary.getIssuesSummary() != null) {
                summaryContext.append("Issues: ").append(summary.getIssuesSummary()).append("\n");
            }

            return summaryContext.length() > 0 ? summaryContext.toString() : null;

        } catch (WebClientResponseException e) {
            if (e.getStatusCode().value() == 404) {
                logger.warn("Summary service returned 404 for week {} - no summaries available", weekId);
            } else {
                logger.warn("Error fetching summary for user {} week {}: {}", username, weekId, e.getMessage());
            }
            return null;
        } catch (Exception e) {
            logger.warn("Error fetching summary for user {} week {}: {}", username, weekId, e.getMessage());
            return null;
        }
    }

    private String buildPreviousQAContext(List<QuestionAnswer> previousAnswers) {
        if (previousAnswers == null || previousAnswers.isEmpty()) {
            return null;
        }

        StringBuilder context = new StringBuilder();
        context.append("Previous Q&A context:\n");

        for (QuestionAnswer answer : previousAnswers) {
            // Get the question text
            Optional<Question> questionOpt = questionRepository.findById(answer.getQuestionId());
            if (questionOpt.isPresent()) {
                context.append("Q: ").append(questionOpt.get().getQuestion()).append("\n");
                context.append("A: ").append(answer.getAnswer()).append("\n");
                if (answer.getConfidence() != null) {
                    context.append("Confidence: ").append(answer.getConfidence()).append("\n");
                }
                context.append("\n");
            }
        }

        return context.toString();
    }

    private String buildCombinedSummary(String summaryContext, String previousQAContext) {
        StringBuilder combined = new StringBuilder();

        if (summaryContext != null && !summaryContext.trim().isEmpty()) {
            combined.append(summaryContext);
        }

        if (previousQAContext != null && !previousQAContext.trim().isEmpty()) {
            if (combined.length() > 0) {
                combined.append("\n\n");
            }
            combined.append(previousQAContext);
        }

        // Return null if no context available, otherwise return the combined string
        return combined.length() > 0 ? combined.toString() : null;
    }

    private String getCurrentWeekId() {
        LocalDate now = LocalDate.now();
        WeekFields weekFields = WeekFields.of(Locale.getDefault());
        int weekNumber = now.get(weekFields.weekOfWeekBasedYear());
        int year = now.get(weekFields.weekBasedYear());
        return String.format("%d-W%02d", year, weekNumber);
    }
}
