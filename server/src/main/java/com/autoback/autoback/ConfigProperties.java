package com.autoback.autoback;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@ConfigurationProperties(prefix="app")
@Validated
public class ConfigProperties {
    @NotBlank
    @NotNull
    private String meiliMasterKey;
    @NotBlank
    @NotNull
    private String meiliHost;
    
    public String getMeiliMasterKey() {
        return meiliMasterKey;
    }
    public String getMeiliHost() {
        return meiliHost;
    }
    public void setMeiliMasterKey(String meiliMasterKey) {
        this.meiliMasterKey = meiliMasterKey;
    }
    public void setMeiliHost(String meiliHost) {
        this.meiliHost = meiliHost;
    }

}