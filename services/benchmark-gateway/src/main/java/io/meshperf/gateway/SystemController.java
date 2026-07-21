package io.meshperf.gateway;

import java.time.Instant;
import java.util.Map;
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

    SystemController(RestClient.Builder builder,
                     @Value("${mesh-perf.orchestrator.base-url}") String baseUrl) {
        this.orchestratorClient = builder.baseUrl(baseUrl).build();
    }

    @GetMapping("/ping")
    Map<String, Object> ping() {
        var correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);
        var downstream = orchestratorClient.get()
                .uri("/internal/v1/ping")
                .header(CorrelationIdFilter.HEADER, correlationId)
                .retrieve()
                .body(Map.class);
        return Map.of(
                "service", "benchmark-gateway",
                "status", "UP",
                "timestamp", Instant.now().toString(),
                "downstream", downstream == null ? Map.of() : downstream);
    }
}
