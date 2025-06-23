package de.promptheus.contributions;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class ContributionsApplication {

	public static void main(String[] args) {
		SpringApplication.run(ContributionsApplication.class, args);
	}

}
