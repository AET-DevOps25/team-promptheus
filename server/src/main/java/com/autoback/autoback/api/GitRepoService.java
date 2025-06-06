package com.autoback.autoback.api;


import com.autoback.autoback.CommunicationObjects.*;
import com.autoback.autoback.persistence.entity.*;
import com.autoback.autoback.persistence.repository.GitRepoRepository;
import com.autoback.autoback.persistence.repository.LinkRepository;
import com.autoback.autoback.persistence.repository.PersonalAccessTokenRepository;
import com.autoback.autoback.persistence.repository.QuestionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
public class GitRepoService {
    private final GitRepoRepository gitRepoRepository;
    private final LinkRepository linkRepository;
    private final PersonalAccessTokenRepository patRepository;
    private final QuestionRepository questionRepository;

    @Autowired
    public GitRepoService(GitRepoRepository gitRepoRepository, LinkRepository linkRepository, PersonalAccessTokenRepository patRepository, QuestionRepository questionRepository) {
        this.gitRepoRepository = gitRepoRepository;
        this.linkRepository = linkRepository;
        this.patRepository = patRepository;
        this.questionRepository = questionRepository;
    }

    public LinkConstruct createAccessLinks(PATConstruct patRequest) {
        String repoLink = patRequest.repolink();
        String pat = patRequest.pat();

        //TODO: testing that repolink can be accessed with the pat
        if (repoLink == null || pat == null || repoLink.isEmpty() || pat.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "repo or pat are invalid");
        }

        // we check if a (GitRepo) object already exists by that repolink
        GitRepo repoEntity = gitRepoRepository.findByRepositoryLink(repoLink);
        if (repoEntity == null) {
            // we create a (GitRepo) object
            repoEntity = gitRepoRepository.save(new GitRepo(repoLink));
            patRepository.save(new PersonalAccessToken(repoEntity, pat));
        }

        // we create one link for developer and manager
        Link devLinkEntity = linkRepository.save(new Link(repoEntity, true));
        Link manLinkEntity = linkRepository.save(new Link(repoEntity, false));

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
        List<ContentConstruct> contents=repoEntity.get().getContents().stream().map(ContentConstruct::from).toList();
        return GitRepoInformationConstruct.builder()
                .repoLink(repoEntity.get().getRepositoryLink())
                .isDeveloper(repoLinkEntity.get().isDeveloper())
                .createdAt(repoEntity.get().getCreatedAt())
                .questions(questions)
                .summaries(summaries)
                .contents(contents)
                .build();
    }

    public void createCommitSelection(UUID accessID, SelectionSubmission selection) {
        Optional<Link> repoLinkEntity = linkRepository.findById(accessID);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }
    }

    public void createQuestion(UUID usercode, String question) {
        Optional<Link> repoLinkEntity = linkRepository.findById(usercode);
        if (repoLinkEntity.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id");
        }

        Question q = Question.builder()
                .gitRepositoryId(repoLinkEntity.get().getGitRepositoryId())
                .question(question)
                .build();
        questionRepository.save(q);
    }
}
