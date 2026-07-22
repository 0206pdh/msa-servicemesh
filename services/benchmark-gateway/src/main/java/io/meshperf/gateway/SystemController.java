package io.meshperf.gateway;

import java.time.Instant;
import java.util.Map;
import io.micrometer.tracing.Tracer;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

@RestController
@RequestMapping("/api/v1/system")
class SystemController {
    private final RestClient orchestratorClient;
    private final Tracer tracer;

    SystemController(RestClient.Builder builder,
                     @Value("${mesh-perf.orchestrator.base-url}") String baseUrl,
                     Tracer tracer) {
        this.orchestratorClient = builder.baseUrl(baseUrl).build();
        this.tracer = tracer;
    }

    @GetMapping("/ping")
    Map<String, Object> ping() {
        var correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);
        var runId = MDC.get(CorrelationIdFilter.RUN_MDC_KEY);
        var request = orchestratorClient.get().uri("/internal/v1/ping").header(CorrelationIdFilter.HEADER, correlationId);
        if (runId != null && !"none".equals(runId)) request.header(CorrelationIdFilter.RUN_HEADER, runId);
        var downstream = request.retrieve().body(Map.class);
        return Map.of(
                "service", "benchmark-gateway",
                "status", "UP",
                "traceId", tracer.currentSpan().context().traceId(),
                "timestamp", Instant.now().toString(),
                "downstream", downstream == null ? Map.of() : downstream);
    }
}
