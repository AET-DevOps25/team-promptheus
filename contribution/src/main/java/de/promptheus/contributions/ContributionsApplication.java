package de.promptheus.contributions;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@OpenAPIDefinition(
  info = @Info(title = "Prompteus Contributions", version = "1.0.0", license = @License(name = "MIT", url = "https://opensource.org/licenses/MIT")),
  servers = { @io.swagger.v3.oas.annotations.servers.Server(url = "https://prompteus.ai", description = "Production server") },
  security = {}
)
@SpringBootApplication
@EnableScheduling
public class ContributionsApplication {

  public static void main(String[] args) {
    SpringApplication.run(ContributionsApplication.class, args);
  }
}
