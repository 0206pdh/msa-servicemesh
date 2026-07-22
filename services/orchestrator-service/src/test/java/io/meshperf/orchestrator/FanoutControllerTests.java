package io.meshperf.orchestrator;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;

class FanoutControllerTests {
    @Test
    void rejectsAggregateMemoryOverSafetyLimit() {
        var controller = new FanoutController(RestClient.builder(), "http://localhost:1");
        var request = new FanoutController.Request(64, FanoutController.Mode.PARALLEL, 1000, true,
                Map.of("memoryBytes", 67_108_864, "seed", 1));
        assertThatThrownBy(() -> controller.fanout(request, mock(HttpServletRequest.class)))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("256 MiB");
    }
}
