package io.meshperf.orchestrator;

import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/v1")
class InternalPingController {
    @GetMapping("/ping")
    Map<String, Object> ping(HttpServletRequest request) {
        return Map.of(
                "service", "orchestrator-service",
                "status", "UP",
                "correlationId", request.getHeader(CorrelationIdFilter.HEADER),
                "timestamp", Instant.now().toString());
    }
}
