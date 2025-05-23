package com.autoback.autoback.api;


import com.autoback.autoback.LinkConstruct;
import com.autoback.autoback.PATConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class ServiceRest {


    private Map<String, String> repo2patmapping = new HashMap<>();
    private Map<LinkConstruct, String> linkconstruct2repomapping = new HashMap<LinkConstruct, String>();

    //@Value("parametername")
    //private String testvalue;

    public ServiceRest() {


    }

    public Optional<LinkConstruct> getLinkConstruct(PATConstruct patrequest) {

        String repolink = patrequest.repolink();
        String pat = patrequest.pat();

        if (repo2patmapping.containsKey(repolink)) {
            return Optional.empty();
        }

        //TODO: testing the repolink with the PAT

        repo2patmapping.put(repolink, pat);

        // TODO: handle this with the db
        UUID uuid_dev = UUID.randomUUID();
        String uuidstring_dev = uuid_dev.toString();
        UUID uuid_man = UUID.randomUUID();
        String uuidstring_man = uuid_man.toString();
        LinkConstruct lc = new LinkConstruct(uuidstring_dev,uuidstring_man);

        linkconstruct2repomapping.put(lc, repolink);

        return Optional.of(lc);

    }


}
