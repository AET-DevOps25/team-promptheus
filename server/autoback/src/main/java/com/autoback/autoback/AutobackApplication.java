package com.autoback.autoback;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

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


	/*
	@GetMapping("/getsummaryselectionfordev")
	public ResponseEntity<ContributionOffering> askForContributionSelectingOfDevelopers(@RequestParam(value = "devuuid") String uuid){

		return
	}
	*/

}
