package io.meshperf.orchestrator;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

@RestController
@RequestMapping("/api/v1/workloads")
class PayloadProxyController {
    private final RestClient workload;
    PayloadProxyController(RestClient.Builder builder, @Value("${mesh-perf.workload.base-url}") String baseUrl) {
        workload = builder.baseUrl(baseUrl).build();
    }

    @PostMapping("/payload")
    ResponseEntity<Map> payload(@RequestBody Map<String, Object> body, HttpServletRequest incoming) {
        var call = workload.post().uri("/api/v1/workloads/payload")
                .header(CorrelationIdFilter.HEADER, incoming.getHeader(CorrelationIdFilter.HEADER))
                .header(CorrelationIdFilter.RUN_HEADER, incoming.getHeader(CorrelationIdFilter.RUN_HEADER));
        var deadline = incoming.getHeader(ChainController.DEADLINE);
        if (deadline != null) call.header(ChainController.DEADLINE, deadline);
        return ResponseEntity.ok(call.body(body).retrieve().body(Map.class));
    }
}
