package io.meshperf.workload;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.io.ByteArrayOutputStream;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import java.util.SplittableRandom;
import java.util.zip.GZIPOutputStream;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/workloads")
class PayloadController {
    private static final int MAX_BYTES = 10_485_760;
    private static final int CHUNK_BYTES = 16_384;

    enum Mode { BUFFERED, STREAMING }
    enum Compression { IDENTITY, GZIP }
    record Request(@Min(0) @Max(MAX_BYTES) int sizeBytes, long seed, @NotNull Mode mode,
                   @NotNull Compression compression, boolean includeBody) {}
    record Result(int sizeBytes, String checksum, Mode mode, Compression compression, String bodyBase64) {}

    @PostMapping("/payload")
    Result payload(@Valid @RequestBody Request request) {
        var original = request.mode() == Mode.BUFFERED
                ? deterministicBytes(request.sizeBytes(), request.seed())
                : deterministicBytesInChunks(request.sizeBytes(), request.seed());
        var encoded = request.compression() == Compression.GZIP ? gzip(original) : original;
        return new Result(request.sizeBytes(), sha256(original), request.mode(), request.compression(),
                request.includeBody() ? Base64.getEncoder().encodeToString(encoded) : null);
    }

    static byte[] deterministicBytes(int size, long seed) {
        var bytes = new byte[size];
        new SplittableRandom(seed).nextBytes(bytes);
        return bytes;
    }

    private static byte[] deterministicBytesInChunks(int size, long seed) {
        var result = new ByteArrayOutputStream(size);
        var random = new SplittableRandom(seed);
        var remaining = size;
        while (remaining > 0) {
            var chunk = new byte[Math.min(CHUNK_BYTES, remaining)];
            random.nextBytes(chunk);
            result.writeBytes(chunk);
            remaining -= chunk.length;
        }
        return result.toByteArray();
    }

    private static byte[] gzip(byte[] bytes) {
        try {
            var output = new ByteArrayOutputStream();
            try (var gzip = new GZIPOutputStream(output)) { gzip.write(bytes); }
            return output.toByteArray();
        } catch (Exception exception) { throw new IllegalStateException("payload compression failed", exception); }
    }

    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (Exception exception) { throw new IllegalStateException(exception); }
    }
}
