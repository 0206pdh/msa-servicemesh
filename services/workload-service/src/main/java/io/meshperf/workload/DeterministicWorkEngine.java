package io.meshperf.workload;

import io.micrometer.core.instrument.MeterRegistry;
import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.SplittableRandom;
import org.springframework.stereotype.Service;

@Service
class DeterministicWorkEngine {
    private final MeterRegistry meters;
    DeterministicWorkEngine(MeterRegistry meters) { this.meters = meters; }

    TargetWorkModels.TargetWorkResult execute(TargetWorkModels.TargetWorkRequest request, String instance) {
        var started = System.nanoTime();
        var work = request.work();
        var random = new SplittableRandom(work.seed());
        if (random.nextDouble() < work.errorRate()) {
            meters.counter("meshperf.workload.executions", "outcome", "injected_error").increment();
            throw new InjectedWorkException("deterministic injected failure");
        }
        var delay = sampledDelay(work, random);
        sleep(delay);
        burnCpu(work.cpuMillis());
        var allocated = deterministicBytes(work.memoryBytes(), work.seed());
        sleep(work.blockingIoMs());
        var response = deterministicBytes(request.responseBytes(), work.seed() ^ 0x5DEECE66DL);
        var checksum = checksum(allocated, response, work.seed());
        var elapsed = (System.nanoTime() - started) / 1_000_000.0;
        meters.counter("meshperf.workload.executions", "outcome", "completed").increment();
        meters.summary("meshperf.workload.elapsed", "distribution", work.delayDistribution().name()).record(elapsed);
        return new TargetWorkModels.TargetWorkResult(instance, elapsed, delay, work.cpuMillis(), allocated.length,
                work.blockingIoMs(), checksum, work.seed());
    }

    private static long sampledDelay(TargetWorkModels.WorkSpec work, SplittableRandom random) {
        if (work.delayMs() == 0) return 0;
        return switch (work.delayDistribution()) {
            case FIXED -> work.delayMs();
            case NORMAL -> Math.min(60_000, Math.max(0, Math.round(work.delayMs() + gaussian(random) * work.delayMs() * 0.15)));
            case EXPONENTIAL -> Math.min(60_000, Math.max(0, Math.round(-Math.log(1.0 - random.nextDouble()) * work.delayMs())));
        };
    }

    private static double gaussian(SplittableRandom random) {
        var u1 = Math.max(Double.MIN_VALUE, random.nextDouble());
        return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * random.nextDouble());
    }

    private static void sleep(long millis) {
        if (millis == 0) return;
        try { Thread.sleep(millis); }
        catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new WorkCancelledException("work interrupted", e); }
    }

    private static void burnCpu(long millis) {
        var deadline = System.nanoTime() + millis * 1_000_000L;
        long value = 0x9E3779B97F4A7C15L;
        while (System.nanoTime() < deadline) value = Long.rotateLeft(value ^ 0xC2B2AE3D27D4EB4FL, 13);
        if (value == 0) throw new IllegalStateException("unreachable guard");
    }

    private static byte[] deterministicBytes(int size, long seed) {
        var bytes = new byte[size];
        new SplittableRandom(seed).nextBytes(bytes);
        return bytes;
    }

    private static String checksum(byte[] memory, byte[] response, long seed) {
        try {
            var digest = MessageDigest.getInstance("SHA-256");
            digest.update(memory); digest.update(response); digest.update(ByteBuffer.allocate(Long.BYTES).putLong(seed).array());
            return HexFormat.of().formatHex(digest.digest());
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    static class InjectedWorkException extends RuntimeException { InjectedWorkException(String message) { super(message); } }
    static class WorkCancelledException extends RuntimeException { WorkCancelledException(String message, Throwable cause) { super(message, cause); } }
}
