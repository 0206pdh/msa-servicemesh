package io.meshperf.producer;
import java.time.Instant;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
@RestController
@RequestMapping("/internal/v1")
class ServiceInfoController {
    @GetMapping("/ping")
    Map<String, String> ping() { return Map.of("service", "producer-service", "status", "UP", "timestamp", Instant.now().toString()); }
}

