package com.autoback.autoback.api;


import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import com.autoback.autoback.CommunicationObjects.PATConstruct;
import com.autoback.autoback.CommunicationObjects.UserCodeConstruct;
import com.autoback.autoback.CommunicationObjects.SearchConstruct;
import com.autoback.autoback.CommunicationObjects.UserConstruct;
import org.springframework.stereotype.Service;
import com.meilisearch.sdk.model.SearchResult;
import com.meilisearch.sdk.Index;
import com.meilisearch.sdk.Client;
import com.meilisearch.sdk.Config;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class ServiceRest {
    private final Client client;

    // todo: replace with db
    private Map<String, String> repo2patmapping = new HashMap<>();
    private Map<LinkConstruct, String> linkconstruct2repomapping = new HashMap<LinkConstruct, String>();

    public ServiceRest() {
        String meiliHost = System.getenv("MEILI_HOST");
        if (meiliHost== null){
            meiliHost="http://localhost:7700";
        }
        String meiliMasterKey = System.getenv("MEILI_MASTER_KEY");
        if (meiliMasterKey== null){
            meiliMasterKey="CHANGE_ME_CHANGE_ME";
        }
        client = new Client(new Config(meiliHost, meiliMasterKey));
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

    public Optional<UserConstruct> getUserConstruct(UserCodeConstruct userrequest) {

        String usercode = userrequest.usercode();

        if (!(usercode.contains("_"))) {
            return Optional.empty();
        } else {

            String rgx = "_";
            String[] components = usercode.split(rgx);

            if (repo2patmapping.containsKey(components[0])){
                // repo uuid exists.
                String reponame = "somereponame";
                String role = components[1];
                if (role.equals("100") || role.equals("200") ){

                    // checks passed.

                    UserConstruct userConstruct = new UserConstruct(reponame,role);
                    return Optional.of(userConstruct);
                }

            }

            //usercode.split();
        }

        return Optional.empty();
    }
    
    public SearchResult search(SearchConstruct searchConstruct) {
        Index index = client.index("content");
        return index.search(searchConstruct.query());
    }
}
