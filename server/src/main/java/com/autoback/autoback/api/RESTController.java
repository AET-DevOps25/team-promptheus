package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import com.autoback.autoback.CommunicationObjects.PATConstruct;
import com.autoback.autoback.CommunicationObjects.UserCodeConstruct;
import com.autoback.autoback.CommunicationObjects.UserConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.Buffer;
import java.nio.ByteBuffer;
import java.util.*;

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

    @Operation(summary = "Get all foos")
    @PostMapping("/providePAT")
    public ResponseEntity<LinkConstruct> registerPAT(@RequestBody PATConstruct patrequest){

        Optional<LinkConstruct> lc = serviceRest.getLinkConstruct(patrequest);
        if (lc.isPresent()) {
            return ResponseEntity.status(HttpStatus.OK).body(lc.get());
        } else {
            return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
    }

    @PostMapping("/uuidmappingtodata")
    public ResponseEntity<UserConstruct> uuidMappingToPersoData(@RequestBody UserCodeConstruct userCodeConstruct){
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

    public static void main(String[] args){
        /*
        int dbuuid = 243232;

        ByteBuffer bb = ByteBuffer.allocate(16).putInt(dbuuid);

        bb.put((byte) 100); // 100 for developer

        byte[] bbb = bb.array();
        String asdf = Base64.getEncoder().encodeToString(bbb);
        System.out.println(asdf);
        */

        UUID uuid = UUID.randomUUID();

        String uuidstring = uuid.toString();


        uuidstring = uuidstring.concat("_");
        uuidstring = uuidstring.concat("100");


        String rgx = "_";
        String[] asdf = uuidstring.split(rgx);


        System.out.println(asdf[0]);






    }

    


}
