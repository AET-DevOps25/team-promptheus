package de.tum.promptheus

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class PromptheusApplication

fun main(args: Array<String>) {
	runApplication<PromptheusApplication>(*args)
}
