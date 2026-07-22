package io.meshperf.worker;

record BenchmarkTaskEvent(
        String eventId,
        String experimentRunId,
        String createdAt,
        TaskBody task
) {
    record TaskBody(
            String idempotencyKey,
            int processingMillis,
            int payloadBytes,
            String payloadBase64,
            long seed
    ) {
    }
}
