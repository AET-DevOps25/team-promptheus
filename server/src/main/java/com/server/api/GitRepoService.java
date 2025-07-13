package com.server.api;

import com.server.CommunicationObjects.*;
import com.server.persistence.entity.*;
import com.server.persistence.repository.*;
import com.server.service.QuestionAnswerService;
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
public class GitRepoService {

    private final GitRepoRepository gitRepoRepository;
    private final LinkRepository linkRepository;
    private final PersonalAccessTokenRepository patRepository;
    private final PersonalAccessToken2GitRepoRepository pat2gitRepository;
    private final QuestionRepository questionRepository;
    private final GitContentRepository gitContentRepository;
    private final QuestionAnswerService questionAnswerService;

    @Autowired
    public GitRepoService(
        GitRepoRepository gitRepoRepository,
        LinkRepository linkRepository,
        PersonalAccessTokenRepository patRepository,
        PersonalAccessToken2GitRepoRepository pat2gitRepository,
        QuestionRepository questionRepository,
        GitContentRepository gitContentRepository,
        QuestionAnswerService questionAnswerService
    ) {
        this.gitRepoRepository = gitRepoRepository;
        this.linkRepository = linkRepository;
        this.patRepository = patRepository;
        this.pat2gitRepository = pat2gitRepository;
        this.questionRepository = questionRepository;
        this.gitContentRepository = gitContentRepository;
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

    public void createQuestion(UUID usercode, String question, String username) {
        Optional<Link> repoLinkEntity = linkRepository.findById(usercode);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }

        // Get repository information for processing
        Optional<GitRepo> repoEntity = gitRepoRepository.findById(repoLinkEntity.get().getGitRepositoryId());
        if (repoEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "repository not found");
        }

        // Save the question first
        Question q = Question.builder().gitRepositoryId(repoLinkEntity.get().getGitRepositoryId()).question(question).build();
        Question savedQuestion = questionRepository.save(q);

        // Use the provided username and current week
        String weekId = getCurrentWeekId();

        // Trigger async processing with GenAI and Summary services
        questionAnswerService.processQuestionAsync(
            savedQuestion.getId(),
            repoEntity.get().getRepositoryLink(),
            username,
            weekId
        );
    }

    private String getCurrentWeekId() {
        java.time.LocalDate now = java.time.LocalDate.now();
        java.time.temporal.WeekFields weekFields = java.time.temporal.WeekFields.of(java.util.Locale.getDefault());
        int weekNumber = now.get(weekFields.weekOfWeekBasedYear());
        int year = now.get(weekFields.weekBasedYear());
        return String.format("%d-W%02d", year, weekNumber);
    }
}
