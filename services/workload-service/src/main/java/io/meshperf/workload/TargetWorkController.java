package io.meshperf.workload;

import jakarta.validation.Valid;
import java.util.Map;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/workloads")
class TargetWorkController {
    private final DeterministicWorkEngine engine;
    private final String role;
    TargetWorkController(DeterministicWorkEngine engine, @Value("${mesh-perf.workload-role}") String role) { this.engine = engine; this.role = role; }

    @PostMapping("/target")
    TargetWorkModels.TargetWorkResult target(@Valid @RequestBody TargetWorkModels.TargetWorkRequest request) {
        return engine.execute(request, role);
    }

    @ExceptionHandler(DeterministicWorkEngine.InjectedWorkException.class)
    ResponseEntity<Map<String, Object>> injected(DeterministicWorkEngine.InjectedWorkException error) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                "code", "INJECTED_FAILURE", "message", error.getMessage(),
                "correlationId", value(CorrelationIdFilter.MDC_KEY), "experimentRunId", value(CorrelationIdFilter.RUN_MDC_KEY),
                "retryable", false, "target", role));
    }
    private static String value(String key) { var value = MDC.get(key); return value == null ? "none" : value; }
}
