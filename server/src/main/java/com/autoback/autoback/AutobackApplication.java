package com.autoback.autoback;

import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@SpringBootApplication
@CrossOrigin(origins = "*")
public class AutobackApplication {

	// will be replaced by db
	private Map<String, String> repo2patmapping = new HashMap<>();
	private Map<LinkConstruct, String> linkconstruct2repomapping = new HashMap<LinkConstruct, String>();

	public static void main(String[] args) {
		SpringApplication.run(AutobackApplication.class, args);

	}


}
