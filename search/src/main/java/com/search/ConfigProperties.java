package com.search;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@Setter
@Getter
@ConfigurationProperties(prefix="app")
@Validated
public class ConfigProperties {
    @NotBlank
    @NotNull
    private String meiliMasterKey;
    @NotBlank
    @NotNull
    private String meiliHost;

}
