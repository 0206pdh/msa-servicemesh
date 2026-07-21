# 실험 도메인 모델

## ExperimentSpec

```text
ExperimentSpec
├── id / version / seed
├── question / hypothesis
├── profile: NO_MESH | SIDECAR | AMBIENT | WAYPOINT
├── scenario
├── workloadConfig
├── loadProfile
├── faultSpec: optional
├── environmentConstraints
├── metrics[]
└── invalidationRules[]
```

## ExperimentRun

```text
ExperimentRun
├── runId / specId
├── status
├── commit / imageDigests / chartVersions
├── nodes / resources / placement
├── startedAt / endedAt
├── groundTruth
├── rawResultRefs[]
├── invalidatingFactors[]
└── summaryRef
```

## WorkloadConfig

```text
WorkloadConfig
├── scenarioType
├── hopCount / fanoutCount
├── executionMode: SEQUENTIAL | PARALLEL
├── delayDistribution
├── errorRate
├── payloadBytes
├── cpuMillis / memoryBytes / ioMillis
├── timeoutBudget
└── retryPolicy
```

## ImprovementExperiment

```text
ImprovementExperiment
├── baselineRunIds[]
├── bottleneckClaim
├── supportingEvidence[]
├── independentVariable
├── expectedEffect
├── regressionMetrics[]
├── rollbackThresholds[]
├── afterRunIds[]
└── conclusion: SUPPORTED | REJECTED | INCONCLUSIVE
```

## ResultSummary

before/after는 동일 schema를 사용한다. latency distribution, throughput, error, resource, recovery, telemetry coverage를 포함하며 누락값은 null과 사유로 표현한다.
