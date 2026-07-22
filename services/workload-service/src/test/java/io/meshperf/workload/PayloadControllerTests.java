package io.meshperf.workload;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Base64;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;

class PayloadControllerTests {
    private final PayloadController controller = new PayloadController();

    @Test
    void bufferedAndChunkedGenerationAreDeterministic() {
        var buffered = controller.payload(new PayloadController.Request(100_000, 42,
                PayloadController.Mode.BUFFERED, PayloadController.Compression.IDENTITY, true));
        var streaming = controller.payload(new PayloadController.Request(100_000, 42,
                PayloadController.Mode.STREAMING, PayloadController.Compression.IDENTITY, true));
        assertThat(streaming.checksum()).isEqualTo(buffered.checksum());
        assertThat(streaming.bodyBase64()).isEqualTo(buffered.bodyBase64());
    }

    @Test
    void gzipRoundTripsToDeterministicPayload() throws Exception {
        var result = controller.payload(new PayloadController.Request(1024, 7,
                PayloadController.Mode.BUFFERED, PayloadController.Compression.GZIP, true));
        try (var input = new GZIPInputStream(new java.io.ByteArrayInputStream(Base64.getDecoder().decode(result.bodyBase64())))) {
            assertThat(input.readAllBytes()).isEqualTo(PayloadController.deterministicBytes(1024, 7));
        }
    }
}
