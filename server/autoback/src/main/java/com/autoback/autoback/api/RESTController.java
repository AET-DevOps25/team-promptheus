package com.autoback.autoback.api;

import com.autoback.autoback.LinkConstruct;
import com.autoback.autoback.PATConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class RESTController {

    private final ServiceRest serviceRest;
    // will be replaced by db
    private Map<String, String> repo2patmapping = new HashMap<>();
    private Map<LinkConstruct, String> linkconstruct2repomapping = new HashMap<LinkConstruct, String>();


    @Autowired
    public RESTController(ServiceRest sr){

        serviceRest = sr;


    }


    @PostMapping("/providePAT")
    public ResponseEntity<LinkConstruct> registerPAT(@RequestBody PATConstruct patrequest){

        Optional<LinkConstruct> lc = serviceRest.getLinkConstruct(patrequest);
        if (lc.isPresent()) {
            return ResponseEntity.status(HttpStatus.OK).body(lc.get());
        } else {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }


}
