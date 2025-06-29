package com.search;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import java.util.HashMap;
import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.web.bind.annotation.*;

@OpenAPIDefinition(
  info = @Info(title = "Prompteus Search", version = "1.0.0", license = @License(name = "MIT", url = "https://opensource.org/licenses/MIT")),
  servers = { @io.swagger.v3.oas.annotations.servers.Server(url = "https://prompteus.ai", description = "Production server") },
  security = {}
)
@RestController
@SpringBootApplication
@EnableConfigurationProperties(ConfigProperties.class)
@CrossOrigin(origins = "*")
public class SearchApplication {

  public static void main(String[] args) {
    SpringApplication.run(SearchApplication.class, args);
  }
}
