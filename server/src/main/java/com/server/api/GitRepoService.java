package com.server.api;

import com.server.CommunicationObjects.*;
import com.server.persistence.entity.*;
import com.server.persistence.repository.*;
import com.server.service.QuestionAnswerService;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class GitRepoService {

    private final GitRepoRepository gitRepoRepository;
    private final LinkRepository linkRepository;
    private final PersonalAccessTokenRepository patRepository;
    private final PersonalAccessToken2GitRepoRepository pat2gitRepository;
    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final QuestionAnswerService questionAnswerService;

    @Autowired
    public GitRepoService(
        GitRepoRepository gitRepoRepository,
        LinkRepository linkRepository,
        PersonalAccessTokenRepository patRepository,
        PersonalAccessToken2GitRepoRepository pat2gitRepository,
        QuestionRepository questionRepository,
        QuestionAnswerRepository questionAnswerRepository,
        GitContentRepository gitContentRepository,
        QuestionAnswerService questionAnswerService
    ) {
        this.gitRepoRepository = gitRepoRepository;
        this.linkRepository = linkRepository;
        this.patRepository = patRepository;
        this.pat2gitRepository = pat2gitRepository;
        this.questionRepository = questionRepository;
        this.questionAnswerRepository = questionAnswerRepository;
        this.questionAnswerService = questionAnswerService;
    }

    public LinkConstruct createAccessLinks(PATConstruct patRequest) {
        String repoLink = patRequest.repolink();
        String pat = patRequest.pat();

        //TODO: testing that repolink can be accessed with the pat
        if (repoLink == null || pat == null || repoLink.isBlank() || pat.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "repo or pat are invalid");
        }

        // we check if a (GitRepo) object already exists by that repolink
        GitRepo repoEntity = gitRepoRepository.findByRepositoryLink(repoLink);
        if (repoEntity == null) {
            // we create a (GitRepo) object
            repoEntity = gitRepoRepository.save(GitRepo.builder().repositoryLink(repoLink).build());
            PersonalAccessToken patEntity = patRepository.save(new PersonalAccessToken(pat));
            pat2gitRepository.save(new PersonalAccessTokensGitRepository(patEntity, repoEntity));
        }

        // we create one link for developer and manager
        Link devLinkEntity = linkRepository.save(Link.builder().gitRepositoryId(repoEntity.getId()).isMaintainer(false).build());
        Link manLinkEntity = linkRepository.save(Link.builder().gitRepositoryId(repoEntity.getId()).isMaintainer(true).build());

        // we put the links together in a LinkConstruct and send it
        return LinkConstruct.builder().developerview("/login/" + devLinkEntity.getId().toString()).stakeholderview("/login/" + manLinkEntity.getId().toString()).build();
    }

    public GitRepoInformationConstruct getRepositoryByAccessID(UUID accessID) {
        // access ID (from a user link) is converted to tuple (repoid , role)
        Optional<Link> repoLinkEntity = linkRepository.findById(accessID);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }

        // repoid is converted to [all data about the repo (GitRepo) which contains its name, questions, summaries ....]
        Optional<GitRepo> repoEntity = gitRepoRepository.findById(repoLinkEntity.get().getGitRepositoryId());
        if (repoEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "link does not point to a repository");
        }

        // from that GitRepo object we only return now the link of the repository and the role
        List<QuestionConstruct> questions = repoEntity.get().getQuestions().stream().map(QuestionConstruct::from).toList();
        List<SummaryConstruct> summaries = repoEntity.get().getSummaries().stream().map(SummaryConstruct::from).toList();
        List<ContentConstruct> contents = repoEntity.get().getContents().stream().map(ContentConstruct::from).toList();
        return GitRepoInformationConstruct.builder()
            .repoLink(repoEntity.get().getRepositoryLink())
            .isMaintainer(repoLinkEntity.get().getIsMaintainer())
            .createdAt(repoEntity.get().getCreatedAt())
            .questions(questions)
            .summaries(summaries)
            .contents(contents)
            .build();
    }

    public QuestionAnswerConstruct createQuestion(UUID usercode, String question, String username, Long gitRepositoryId, String weekId) {
        Optional<Link> repoLinkEntity = linkRepository.findById(usercode);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }

        // Determine which repository to use - prioritize gitRepositoryId if provided
        Long targetRepositoryId;
        if (gitRepositoryId != null) {
            // Verify the provided gitRepositoryId is valid and user has access
            Optional<GitRepo> providedRepo = gitRepoRepository.findById(gitRepositoryId);
            if (providedRepo.isEmpty()) {
                throw new ResponseStatusException(HttpStatus.NOT_FOUND, "specified repository not found");
            }
            targetRepositoryId = gitRepositoryId;
        } else {
            // Use repository from usercode link
            targetRepositoryId = repoLinkEntity.get().getGitRepositoryId();
        }

        // Get repository information for processing
        Optional<GitRepo> repoEntity = gitRepoRepository.findById(targetRepositoryId);
        if (repoEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "repository not found");
        }

        // Save the question first
        Question q = Question.builder().gitRepositoryId(targetRepositoryId).question(question).build();
        Question savedQuestion = questionRepository.save(q);

        // Use the provided weekId, or current week as fallback
        String finalWeekId = weekId != null ? weekId : getCurrentWeekId();

        try {
            // Process question synchronously and wait for result
            CompletableFuture<Void> processingFuture = questionAnswerService.processQuestionAsync(
                savedQuestion.getId(),
                repoEntity.get().getRepositoryLink(),
                username,
                finalWeekId
            );

            // Wait for processing to complete (with timeout)
            processingFuture.get(30, java.util.concurrent.TimeUnit.SECONDS);

            // Retrieve the processed answer
            List<QuestionAnswer> answers = questionAnswerRepository.findByQuestionIdIn(List.of(savedQuestion.getId()));
            Optional<QuestionAnswer> answerOpt = answers.stream().findFirst();

            if (answerOpt.isPresent()) {
                return QuestionAnswerConstruct.from(answerOpt.get());
            } else {
                throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Failed to process question - no answer found");
            }

        } catch (java.util.concurrent.TimeoutException e) {
            throw new ResponseStatusException(HttpStatus.REQUEST_TIMEOUT, "Question processing timed out");
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Failed to process question: " + e.getMessage());
        }
    }

    private String getCurrentWeekId() {
        java.time.LocalDate now = java.time.LocalDate.now();
        java.time.temporal.WeekFields weekFields = java.time.temporal.WeekFields.of(java.util.Locale.getDefault());
        int weekNumber = now.get(weekFields.weekOfWeekBasedYear());
        int year = now.get(weekFields.weekBasedYear());
        return String.format("%d-W%02d", year, weekNumber);
    }

    public List<QuestionAnswerConstruct> getQuestionsAndAnswersForUserWeek(String username, String weekId) {
        List<QuestionAnswer> answers = questionAnswerRepository.findByUserNameAndWeekIdOrderByAskedAtDesc(username, weekId);
        return answers.stream()
            .map(QuestionAnswerConstruct::from)
            .toList();
    }
}
