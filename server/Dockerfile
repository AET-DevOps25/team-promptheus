# Stage 1: Build the application
FROM --platform=$BUILDPLATFORM gradle:8.14-jdk21 AS build
WORKDIR /app
COPY build.gradle settings.gradle ./
COPY src ./src
RUN gradle bootJar --no-daemon

# Stage 1.5 buisybox
FROM busybox AS busybox
# Stage 2: Run the application
FROM gcr.io/distroless/java21-debian12
WORKDIR /app
COPY --from=busybox /bin/wget /bin/wget
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8080
HEALTHCHECK --start-period=5s --interval=2s --timeout=3s --retries=2 CMD ["/bin/wget", "-qO-", "--tries=1", "http://localhost:8080/actuator/health"]
ENTRYPOINT ["java", "-jar", "app.jar"]
