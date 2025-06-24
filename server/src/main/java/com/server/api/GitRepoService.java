package com.server.api;


import com.server.CommunicationObjects.*;
import com.server.persistence.entity.*;
import com.server.persistence.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

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

@Service
public class GitRepoService {
    private final GitRepoRepository gitRepoRepository;
    private final LinkRepository linkRepository;
    private final PersonalAccessTokenRepository patRepository;
    private final PersonalAccessToken2GitRepoRepository pat2gitRepository;
    private final QuestionRepository questionRepository;
    private final GitContentRepository gitContentRepository;

    @Autowired
    public GitRepoService(GitRepoRepository gitRepoRepository, LinkRepository linkRepository, PersonalAccessTokenRepository patRepository, PersonalAccessToken2GitRepoRepository pat2gitRepository, QuestionRepository questionRepository, GitContentRepository gitContentRepository) {
        this.gitRepoRepository = gitRepoRepository;
        this.linkRepository = linkRepository;
        this.patRepository = patRepository;
        this.pat2gitRepository = pat2gitRepository;
        this.questionRepository = questionRepository;
        this.gitContentRepository = gitContentRepository;
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
        return LinkConstruct.builder().developerview(devLinkEntity.getId().toString()).stakeholderview(manLinkEntity.getId().toString()).build();
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
        return GitRepoInformationConstruct.builder().repoLink(repoEntity.get().getRepositoryLink()).isMaintainer(repoLinkEntity.get().getIsMaintainer()).createdAt(repoEntity.get().getCreatedAt()).questions(questions).summaries(summaries).contents(contents).build();
    }

    public void createCommitSelection(UUID accessID, SelectionSubmission selection) {
        Optional<Link> repoLinkEntity = linkRepository.findById(accessID);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }
        Instant weekStart = Instant.now().atZone(ZoneId.systemDefault()).with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY)).truncatedTo(ChronoUnit.DAYS).toInstant();
        Set<Content> validContent = gitContentRepository.findDistinctByCreatedAtAfterAndGitRepositoryId(weekStart, repoLinkEntity.get().getGitRepositoryId());
        if (!validContent.stream().map(Content::getId).collect(Collectors.toSet()).containsAll(selection.selection()))
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "please make sure that all selected content exists for the current week");

        // below would be the SQL below, but JPA is being stubborn
        // UPDATE Content SET is_selected = CASE WHEN id IN (:ids) THEN true ELSE false END WHERE createdAt >= date_trunc('week', now())
        for (Content c : validContent) {
            c.setIsSelected(selection.selection().contains(c.getId()));
            gitContentRepository.save(c);
        }
    }

    public void createQuestion(UUID usercode, String question) {
        Optional<Link> repoLinkEntity = linkRepository.findById(usercode);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }

        Question q = Question.builder().gitRepositoryId(repoLinkEntity.get().getGitRepositoryId()).question(question).build();
        questionRepository.save(q);
    }
}
