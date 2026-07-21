FROM gradle:9.1.0-jdk25 AS build
WORKDIR /workspace
COPY settings.gradle.kts build.gradle.kts ./
COPY gradlew gradlew.bat ./
COPY gradle gradle
COPY src src
RUN ./gradlew --no-daemon bootJar
FROM eclipse-temurin:25-jre-alpine
RUN addgroup -S meshperf && adduser -S meshperf -G meshperf
USER meshperf
WORKDIR /app
COPY --from=build /workspace/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
