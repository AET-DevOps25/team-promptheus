package com.server;

import com.server.CommunicationObjects.LinkConstruct;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import java.util.HashMap;
import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

@OpenAPIDefinition(
  info = @Info(title = "Prompteus Server", version = "1.0.0", license = @License(name = "MIT", url = "https://opensource.org/licenses/MIT")),
  servers = { @io.swagger.v3.oas.annotations.servers.Server(url = "https://prompteus.ai", description = "Production server") },
  security = {}
)
@RestController
@SpringBootApplication
@CrossOrigin(origins = "*")
public class ServerApplication {

  public static void main(String[] args) {
    SpringApplication.run(ServerApplication.class, args);
  }
}
