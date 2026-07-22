package io.meshperf.worker;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import io.micrometer.core.instrument.MeterRegistry;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.UUID;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

@Component
class TaskWorker {
    private static final int MAX_KEYS = 100_000;

    private final Cache<String, Boolean> processed = Caffeine.newBuilder()
            .maximumSize(MAX_KEYS)
            .build();
    private final MeterRegistry meters;
    private final ObjectMapper json;
    private final KafkaTemplate<String, String> kafka;

    TaskWorker(MeterRegistry meters, ObjectMapper json, KafkaTemplate<String, String> kafka) {
        this.meters = meters;
        this.json = json;
        this.kafka = kafka;
    }

    @KafkaListener(topics = "meshperf.tasks.v1")
    void consume(String payload) {
        var event = json.readValue(payload, BenchmarkTaskEvent.class);
        var task = event.task();
        if (processed.asMap().putIfAbsent(task.idempotencyKey(), Boolean.TRUE) != null) {
            meters.counter("meshperf.worker.tasks", "outcome", "duplicate").increment();
            publishResult(event, "DUPLICATE", 0, checksum(task.payloadBase64()));
            return;
        }

        var started = System.nanoTime();
        meters.summary("meshperf.worker.task.age.ms").record(Math.max(0, java.time.Duration.between(Instant.parse(event.createdAt()), Instant.now()).toMillis()));
        try {
            Thread.sleep(task.processingMillis());
            var elapsed = (System.nanoTime() - started) / 1_000_000.0;
            meters.timer("meshperf.worker.processing").record((long)(elapsed * 1_000_000), java.util.concurrent.TimeUnit.NANOSECONDS);
            meters.counter("meshperf.worker.tasks", "outcome", "completed").increment();
            publishResult(event, "COMPLETED", elapsed, checksum(task.payloadBase64()));
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            meters.counter("meshperf.worker.tasks", "outcome", "failed").increment();
            publishResult(event, "FAILED", (System.nanoTime() - started) / 1_000_000.0, "none");
        }
    }

    private void publishResult(BenchmarkTaskEvent source, String status, double elapsed, String checksum) {
        var result = new TaskResult(UUID.randomUUID().toString(), source.eventId(), source.experimentRunId(), source.task().idempotencyKey(),
                "worker-service", status, Instant.now().toString(), elapsed, checksum, status.equals("FAILED") ? "INTERRUPTED" : null, 1);
        kafka.send("meshperf.task-results.v1", source.task().idempotencyKey(), json.writeValueAsString(result));
    }

    private static String checksum(String payload) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Base64.getDecoder().decode(payload))); }
        catch (Exception exception) { throw new IllegalArgumentException("invalid task payload", exception); }
    }

    record TaskResult(String eventId, String sourceEventId, String experimentRunId, String idempotencyKey, String worker,
                      String status, String processedAt, double processingMillis, String checksum, String errorCode, int attempt) {}
}
