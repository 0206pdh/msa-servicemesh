package io.meshperf.worker;

import static org.assertj.core.api.Assertions.assertThat;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;
import static org.mockito.Mockito.mock;
import org.springframework.kafka.core.KafkaTemplate;

class TaskWorkerTests {
    @Test
    void duplicateIdempotencyKeyIsNotProcessedTwice() {
        var meters = new SimpleMeterRegistry();
        var json = JsonMapper.builder().build();
        var worker = new TaskWorker(meters, json, mock(KafkaTemplate.class));
        var task = new BenchmarkTaskEvent("event", "run", "2026-07-22T00:00:00Z",
                new BenchmarkTaskEvent.TaskBody("same-key", 0, 0, "", 1));
        var payload = json.writeValueAsString(task);
        worker.consume(payload);
        worker.consume(payload);
        assertThat(meters.counter("meshperf.worker.tasks", "outcome", "completed").count()).isEqualTo(1);
        assertThat(meters.counter("meshperf.worker.tasks", "outcome", "duplicate").count()).isEqualTo(1);
    }
}
