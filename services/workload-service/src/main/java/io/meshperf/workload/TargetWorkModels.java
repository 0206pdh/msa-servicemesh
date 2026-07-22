package io.meshperf.workload;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

final class TargetWorkModels {
    private TargetWorkModels() {}

    enum DelayDistribution { FIXED, NORMAL, EXPONENTIAL }

    record WorkSpec(
            @Min(0) @Max(60_000) long delayMs,
            @NotNull DelayDistribution delayDistribution,
            @DecimalMin("0.0") @DecimalMax("1.0") double errorRate,
            @Min(0) @Max(10_000) long cpuMillis,
            @Min(0) @Max(67_108_864) int memoryBytes,
            @Min(0) @Max(10_000) long blockingIoMs,
            long seed) {}

    record TargetWorkRequest(@NotNull @Valid WorkSpec work, @Min(0) @Max(10_485_760) int responseBytes) {}

    record TargetWorkResult(String instance, double elapsedMs, long delayAppliedMs,
                            long cpuAppliedMs, int allocatedBytes, long blockingIoAppliedMs,
                            String checksum, long seed) {}
}
