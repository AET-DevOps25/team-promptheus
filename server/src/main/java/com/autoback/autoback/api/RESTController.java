package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import com.autoback.autoback.CommunicationObjects.PATConstruct;
import com.autoback.autoback.CommunicationObjects.SearchConstruct;
import com.autoback.autoback.CommunicationObjects.GitRepoInformationConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.meilisearch.sdk.model.SearchResult;

import java.util.*;

@RestController
@RequestMapping("/api/repositories")
public class RESTController {
    private final GitRepoService gitRepoService;

    @Autowired
    public RESTController(GitRepoService gitRepoService){
        this.gitRepoService = gitRepoService;
    }

    @PostMapping("/PAT")
    public ResponseEntity<LinkConstruct> createFromPAT(@RequestBody PATConstruct patRequest){
        // registers a new repository with a PAT
        Optional<LinkConstruct> lc = gitRepoService.createAccessLinks(patRequest);
        if (lc.isPresent()) {
            return ResponseEntity.status(HttpStatus.OK).body(lc.get());
        } else {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
        }
    }

    @GetMapping("/{usercode}")
    /// responds with the repo and role the uuid is referring to
    public ResponseEntity<GitRepoInformationConstruct> getGitRepository(@PathVariable UUID usercode){
        // given a user link, we obtain the information which will be set to a cookie client-side
        Optional<GitRepoInformationConstruct> gitRepository = gitRepoService.getRepositoryByAccessID(usercode);
        if (gitRepository.isPresent()) {
            return ResponseEntity.status(HttpStatus.OK).body(gitRepository.get());
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }
    }

    @GetMapping("/search")
    public ResponseEntity<SearchResult> search(@RequestParam String query){
        SearchResult results = serviceRest.search(new SearchConstruct(query));
        return ResponseEntity.status(HttpStatus.OK).body(results);
    }
}
