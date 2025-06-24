package com.autoback.autoback;

import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

import java.util.HashMap;
import java.util.Map;

@RestController
@SpringBootApplication
@EnableConfigurationProperties(ConfigProperties.class)
@CrossOrigin(origins = "*")
public class AutobackApplication {
	public static void main(String[] args) {
		SpringApplication.run(AutobackApplication.class, args);
	}
}
