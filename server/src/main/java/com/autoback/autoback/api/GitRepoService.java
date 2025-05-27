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
        LinkConstruct lc = new LinkConstruct(devLinkEntity.getId().toString(), manLinkEntity.getId().toString());
        return Optional.of(lc);
    }

    public Optional<GitRepoInformationConstruct> getRepositoryByAccessID(UUID accessID) {

        // access ID (from user link) is converted to tuple (repoid , role) 
        Optional<Link> repoLinkEntity = linkRepository.findById(accessID); 
        if (repoLinkEntity.isEmpty()) {
            return Optional.empty();
        }

        // repoid is converted to [all data about the repo (GitRepo) which contains its name, questions, summaries ....]
        Optional<GitRepo> repoEntity = gitRepoRepository.findById(repoLinkEntity.get().getGitRepositoryId());
        if (repoEntity.isEmpty()) {
            return Optional.empty();
        }

        // from that GitRepo object we only return now the link of the repository and the role
        return Optional.of(new GitRepoInformationConstruct(
                repoEntity.get().getRepositoryLink(),
                repoLinkEntity.get().isDeveloper()
        ));
    }
}
