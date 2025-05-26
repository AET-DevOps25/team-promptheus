package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import com.autoback.autoback.CommunicationObjects.PATConstruct;
import com.autoback.autoback.CommunicationObjects.SearchConstruct;
import com.autoback.autoback.CommunicationObjects.UserCodeConstruct;
import com.autoback.autoback.CommunicationObjects.UserConstruct;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import com.meilisearch.sdk.model.SearchResult;

import java.util.Optional;

@RestController
@RequestMapping("/api")
public class RESTController {
    private final ServiceRest serviceRest;
    private final Counter patRegistrationCnt;

    @Autowired
    public RESTController(ServiceRest sr, MeterRegistry registry) {
        serviceRest = sr;
        patRegistrationCnt = Counter.builder("pat_registration_total").description("Total number of personal access tokens registered").register(registry);
    }

    @PostMapping("/providePAT")
    public ResponseEntity<LinkConstruct> registerPAT(@RequestBody PATConstruct patrequest) {

        Optional<LinkConstruct> lc = serviceRest.getLinkConstruct(patrequest);
        if (lc.isPresent()) {
            patRegistrationCnt.increment();
            return ResponseEntity.status(HttpStatus.OK).body(lc.get());
        } else {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }

    @PostMapping("/uuidmappingtodata")
    public ResponseEntity<UserConstruct> uuidMappingToPersoData(@RequestBody UserCodeConstruct userCodeConstruct) {
        // responds with the repo and role the uuid is referring to
        // it does so by decomposing the uuidcode into:
        // uuidcode <-> patternpadding(repouuid,role)
        //
        // patternpadding = repouuid + role
        // we test serverside whether the repo is in the db

        Optional<UserConstruct> usercontent = serviceRest.getUserConstruct(userCodeConstruct);
        if (usercontent.isPresent()) {
            return ResponseEntity.status(HttpStatus.OK).body(usercontent.get());
        } else {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }
    
    @GetMapping("/search")
    public ResponseEntity<SearchResult> search(@RequestParam String query){
        SearchResult results = serviceRest.search(new SearchConstruct(query));
        return ResponseEntity.status(HttpStatus.OK).body(results);
    }
}
