package io.meshperf.workload;

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
@RequestMapping("/internal/v1")
class ChainHopController {
    static final String DEADLINE = "X-Request-Deadline-Epoch-Ms";
    private final DeterministicWorkEngine engine;
    private final RestClient next;
    private final String role;

    ChainHopController(DeterministicWorkEngine engine, RestClient.Builder builder,
                       @Value("${mesh-perf.next-base-url}") String nextBaseUrl,
                       @Value("${mesh-perf.workload-role}") String role) {
        this.engine = engine;
        this.next = builder.baseUrl(nextBaseUrl).build();
        this.role = role;
    }

    @PostMapping("/chain-hop")
    ResponseEntity<Map<String, Object>> hop(@RequestBody HopRequest body, HttpServletRequest incoming) {
        if (expired(incoming)) return deadline(body.completedHops());
        var target = engine.execute(new TargetWorkModels.TargetWorkRequest(body.work(), body.payloadBytes()), role);
        var completed = body.completedHops() + 1;
        if (expired(incoming)) return deadline(completed);
        if (body.remainingHops() == 1) return ResponseEntity.ok(result("COMPLETED", completed, target.checksum()));
        var call = next.post().uri("/internal/v1/chain-hop")
                .header(CorrelationIdFilter.HEADER, incoming.getHeader(CorrelationIdFilter.HEADER))
                .header(CorrelationIdFilter.RUN_HEADER, incoming.getHeader(CorrelationIdFilter.RUN_HEADER));
        var deadline = incoming.getHeader(DEADLINE);
        if (deadline != null) call.header(DEADLINE, deadline);
        return ResponseEntity.ok(call.body(new HopRequest(body.remainingHops() - 1, completed, body.payloadBytes(), body.work()))
                .retrieve().body(Map.class));
    }

    record HopRequest(int remainingHops, int completedHops, int payloadBytes, TargetWorkModels.WorkSpec work) {}
    private static boolean expired(HttpServletRequest request) { var value=request.getHeader(DEADLINE); return value!=null && System.currentTimeMillis()>=Long.parseLong(value); }
    private static ResponseEntity<Map<String,Object>> deadline(int completed) { return ResponseEntity.status(504).body(result("DEADLINE_EXCEEDED", completed, "none")); }
    private static Map<String,Object> result(String status,int completed,String checksum) { return Map.of("status",status,"completedHops",completed,"checksum",checksum); }
}
