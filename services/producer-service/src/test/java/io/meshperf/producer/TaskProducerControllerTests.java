package io.meshperf.producer;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;

import org.junit.jupiter.api.Test;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.web.server.ResponseStatusException;
import tools.jackson.databind.json.JsonMapper;

class TaskProducerControllerTests {
    @Test
    void rejectsAggregatePayloadOverSafetyLimit() {
        var controller = new TaskProducerController(mock(KafkaTemplate.class), JsonMapper.builder().build());
        assertThatThrownBy(() -> controller.publish(new TaskProducerController.Request(10_000, 0, 10_485_760, 1)))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("64 MiB");
    }
}
