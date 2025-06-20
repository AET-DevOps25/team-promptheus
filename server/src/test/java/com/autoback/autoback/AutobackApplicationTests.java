package com.autoback.autoback;

import com.autoback.autoback.api.GitRepoController;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class AutobackApplicationTests {

	@Autowired
	private GitRepoController controller;

	@Disabled
	@Test
	void contextLoads() throws Exception {
		assertThat(controller).isNotNull();
	}
}
