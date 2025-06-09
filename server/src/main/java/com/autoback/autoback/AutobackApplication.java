package com.autoback.autoback;

import com.autoback.autoback.CommunicationObjects.LinkConstruct;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import io.opentelemetry.instrumentation.logback.appender.v1_0.OpenTelemetryAppender;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.autoconfigure.AutoConfiguredOpenTelemetrySdk;

import java.util.HashMap;
import java.util.Map;

@RestController
@SpringBootApplication
@EnableConfigurationProperties(ConfigProperties.class)
@CrossOrigin(origins = "*")
public class AutobackApplication {
	public static void main(String[] args) {
    	OpenTelemetrySdk openTelemetrySdk = AutoConfiguredOpenTelemetrySdk.initialize().getOpenTelemetrySdk()
        OpenTelemetryAppender.install(openTelemetrySdk);
		SpringApplication.run(AutobackApplication.class, args);
	}
}
