package io.meshperf.orchestrator;

import jakarta.servlet.http.HttpServletRequest;
import java.time.Instant;
import java.util.Map;
import io.micrometer.tracing.Tracer;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/v1")
class InternalPingController {
    private final Tracer tracer;
    InternalPingController(Tracer tracer) { this.tracer = tracer; }
    @GetMapping("/ping")
    Map<String, Object> ping(HttpServletRequest request) {
        return Map.of(
                "service", "orchestrator-service",
                "status", "UP",
                "correlationId", request.getHeader(CorrelationIdFilter.HEADER),
                "experimentRunId", request.getHeader(CorrelationIdFilter.RUN_HEADER) == null ? "none" : request.getHeader(CorrelationIdFilter.RUN_HEADER),
                "traceId", tracer.currentSpan().context().traceId(),
                "timestamp", Instant.now().toString());
    }
}
