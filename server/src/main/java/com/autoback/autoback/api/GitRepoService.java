package com.autoback.autoback.api;


import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import com.autoback.autoback.CommunicationObjects.PATConstruct;
import com.autoback.autoback.CommunicationObjects.GitRepoInformationConstruct;
import com.autoback.autoback.persistence.entity.GitRepo;
import com.autoback.autoback.persistence.entity.Link;
import com.autoback.autoback.persistence.entity.PersonalAccessToken;
import com.autoback.autoback.persistence.repository.GitRepoRepository;
import com.autoback.autoback.persistence.repository.LinkRepository;
import com.autoback.autoback.persistence.repository.PersonalAccessTokenRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.UUID;

@Service
public class GitRepoService {
    private final GitRepoRepository gitRepoRepository;
    private final LinkRepository linkRepository;
    private final PersonalAccessTokenRepository patRepository;

    @Autowired
    public GitRepoService(GitRepoRepository gitRepoRepository, LinkRepository linkRepository, PersonalAccessTokenRepository patRepository) {
        this.gitRepoRepository = gitRepoRepository;
        this.linkRepository = linkRepository;
        this.patRepository = patRepository;
    }

    public Optional<LinkConstruct> createAccessLinks(PATConstruct patRequest) {
        String repoLink = patRequest.repolink();
        String pat = patRequest.pat();

        //TODO: testing that repolink can be accessed with the pat
        if (repoLink == null || pat == null || repoLink.isEmpty() || pat.isEmpty()) {
            return Optional.empty();
        }

        GitRepo repoEntity = gitRepoRepository.findByRepositoryLink(repoLink);
        if (repoEntity == null) {
            repoEntity = gitRepoRepository.save(new GitRepo(repoLink));
            patRepository.save(new PersonalAccessToken(repoEntity, pat));
        }

        Link devLinkEntity = linkRepository.save(new Link(repoEntity, true));
        Link manLinkEntity = linkRepository.save(new Link(repoEntity, false));

        LinkConstruct lc = new LinkConstruct(devLinkEntity.getId().toString(), manLinkEntity.getId().toString());
        return Optional.of(lc);
    }

    public Optional<GitRepoInformationConstruct> getRepositoryByAccessID(UUID accessID) {
        Optional<Link> repoLinkEntity = linkRepository.findById(accessID);
        if (repoLinkEntity.isEmpty()) {
            return Optional.empty();
        }

        Optional<GitRepo> repoEntity = gitRepoRepository.findById(repoLinkEntity.get().getGitRepositoryId());
        if (repoEntity.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new GitRepoInformationConstruct(
                repoEntity.get().getRepositoryLink(),
                repoLinkEntity.get().isDeveloper()
        ));
    }
}
