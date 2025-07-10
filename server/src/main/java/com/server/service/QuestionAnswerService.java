package com.server.service;

import com.server.genai.api.DefaultApi;
import com.server.genai.model.QuestionRequest;
import com.server.genai.model.QuestionResponse;
import com.server.summary.api.SummaryControllerApi;
import com.server.summary.model.Summary;
import com.server.persistence.entity.Question;
import com.server.persistence.entity.QuestionAnswer;
import com.server.persistence.repository.QuestionRepository;
import com.server.persistence.repository.QuestionAnswerRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.temporal.WeekFields;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.CompletableFuture;

@Service
public class QuestionAnswerService {

    private static final Logger logger = LoggerFactory.getLogger(QuestionAnswerService.class);

    private final DefaultApi genaiApi;
    private final SummaryControllerApi summaryApi;
    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;

    @Autowired
    public QuestionAnswerService(
            DefaultApi genaiApi,
            SummaryControllerApi summaryApi,
            QuestionRepository questionRepository,
            QuestionAnswerRepository questionAnswerRepository
    ) {
        this.genaiApi = genaiApi;
        this.summaryApi = summaryApi;
        this.questionRepository = questionRepository;
        this.questionAnswerRepository = questionAnswerRepository;
    }

    @Async
    public CompletableFuture<Void> processQuestionAsync(Long questionId, String repositoryUrl) {
        try {
            Question question = questionRepository.findById(questionId)
                    .orElseThrow(() -> new RuntimeException("Question not found: " + questionId));

            logger.info("Processing question {} for repository {}", questionId, repositoryUrl);

            // Extract repository information from URL
            // Assuming GitHub URL format: https://github.com/owner/repo
            String[] urlParts = repositoryUrl.replace("https://github.com/", "").split("/");
            if (urlParts.length < 2) {
                throw new RuntimeException("Invalid repository URL format: " + repositoryUrl);
            }
            String owner = urlParts[0];
            String repo = urlParts[1];

            // For now, we'll use a default username and current week
            // In a real implementation, you'd extract this from the context
            String username = "defaultuser"; // TODO: Extract from request context
            String weekId = getCurrentWeekId();

            // First, try to get existing summaries to provide context
            List<Summary> summaries = getSummariesForContext(weekId);
            String summaryContext = summaries.isEmpty() ? null :
                summaries.get(0).getOverview(); // Use first summary as context

            // Create question request for GenAI
            QuestionRequest questionRequest = new QuestionRequest()
                    .question(question.getQuestion())
                    .summary(summaryContext);

            // Call GenAI service
            Mono<QuestionResponse> responseMono = genaiApi
                    .askQuestionAboutUserContributionsUsersUsernameWeeksWeekIdQuestionsPost(
                            username, weekId, questionRequest);

            QuestionResponse response = responseMono.block(); // Blocking for simplicity

            if (response != null) {
                // Save the answer
                QuestionAnswer answer = QuestionAnswer.builder()
                        .questionId(questionId)
                        .answer(response.getAnswer())
                        .confidence(response.getConfidence() != null ?
                                response.getConfidence().floatValue() : null)
                        .build();

                questionAnswerRepository.save(answer);
                logger.info("Successfully processed question {} with answer", questionId);
            } else {
                logger.warn("No response received from GenAI service for question {}", questionId);
            }

        } catch (Exception e) {
            logger.error("Error processing question {}: {}", questionId, e.getMessage(), e);

            // Save error response
            QuestionAnswer errorAnswer = QuestionAnswer.builder()
                    .questionId(questionId)
                    .answer("Error processing question: " + e.getMessage())
                    .confidence(0.0f)
                    .build();

            questionAnswerRepository.save(errorAnswer);
        }

        return CompletableFuture.completedFuture(null);
    }

    private String getCurrentWeekId() {
        LocalDate now = LocalDate.now();
        WeekFields weekFields = WeekFields.of(Locale.getDefault());
        int weekNumber = now.get(weekFields.weekOfWeekBasedYear());
        int year = now.get(weekFields.weekBasedYear());
        return String.format("%d-W%02d", year, weekNumber);
    }

    private List<Summary> getSummariesForContext(String weekId) {
        try {
            // Call summary service to get relevant summaries
            return summaryApi.getSummaries(weekId).collectList().block();
        } catch (Exception e) {
            logger.warn("Could not fetch summaries for context: {}", e.getMessage());
            return List.of();
        }
    }
}
