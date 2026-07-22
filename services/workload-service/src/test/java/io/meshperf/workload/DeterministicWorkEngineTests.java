package io.meshperf.workload;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DeterministicWorkEngineTests {
    private final DeterministicWorkEngine engine = new DeterministicWorkEngine(new SimpleMeterRegistry());

    @Test void sameSeedAndConfigProduceSameChecksum() {
        var request = request(42, 0, 1024, 2048);
        var first = engine.execute(request, "target-a");
        var second = engine.execute(request, "target-a");
        assertThat(first.checksum()).isEqualTo(second.checksum());
        assertThat(first.allocatedBytes()).isEqualTo(1024);
    }

    @Test void fixedDelayIsReportedExactly() {
        var request = new TargetWorkModels.TargetWorkRequest(
                new TargetWorkModels.WorkSpec(2, TargetWorkModels.DelayDistribution.FIXED, 0, 0, 0, 0, 1), 0);
        assertThat(engine.execute(request, "target-a").delayAppliedMs()).isEqualTo(2);
    }

    @Test void fullErrorRateAlwaysInjectsFailure() {
        var request = new TargetWorkModels.TargetWorkRequest(
                new TargetWorkModels.WorkSpec(0, TargetWorkModels.DelayDistribution.FIXED, 1, 0, 0, 0, 1), 0);
        assertThatThrownBy(() -> engine.execute(request, "target-a"))
                .isInstanceOf(DeterministicWorkEngine.InjectedWorkException.class);
    }

    private static TargetWorkModels.TargetWorkRequest request(long seed, long delay, int memory, int response) {
        return new TargetWorkModels.TargetWorkRequest(
                new TargetWorkModels.WorkSpec(delay, TargetWorkModels.DelayDistribution.NORMAL, 0, 0, memory, 0, seed), response);
    }
}
