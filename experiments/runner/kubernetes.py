from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote


class KubernetesAdapter:
    """Read-only Kubernetes and Prometheus evidence collector."""

    SYNC_CHAIN_POD_PREFIXES = (
        "benchmark-gateway-",
        "orchestrator-service-",
        "producer-service-",
        "worker-service-",
        "workload-a-",
        "workload-b-",
        "workload-c-",
    )

    def __init__(self, root: Path, spec: dict, command_runner=subprocess.run):
        self.root = root
        self.spec = spec
        self.config = spec.get("kubernetes", {})
        self.namespace = self.config.get("namespace", "benchmark")
        self.command_runner = command_runner
        self.kubeconfig = self.config.get("kubeconfig") or os.getenv("MESHPERF_KUBECONFIG")
        self.prometheus_service = self.config.get(
            "prometheusService", "monitoring-kube-prometheus-prometheus"
        )
        self.prometheus_namespace = self.config.get("prometheusNamespace", "observability")

    def kubectl(self, *args: str, json_output: bool = False):
        command = ["kubectl"]
        if self.kubeconfig:
            command += ["--kubeconfig", self.kubeconfig]
        command += list(args)
        result = self.command_runner(
            command, cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"kubectl failed: {' '.join(args)}: {(result.stderr or '').strip()}")
        output = result.stdout or ""
        return json.loads(output) if json_output else output.strip()

    def prometheus_query(self, query: str) -> dict:
        path = (
            f"/api/v1/namespaces/{self.prometheus_namespace}/services/http:"
            f"{self.prometheus_service}:9090/proxy/api/v1/query?query={quote(query, safe='')}"
        )
        response = self.kubectl("get", "--raw", path, json_output=True)
        if response.get("status") != "success":
            raise RuntimeError(f"Prometheus query failed: {query}")
        return response

    def prometheus_query_range(self, query: str, start: float, end: float, step_seconds: int) -> dict:
        path = (
            f"/api/v1/namespaces/{self.prometheus_namespace}/services/http:"
            f"{self.prometheus_service}:9090/proxy/api/v1/query_range?query={quote(query, safe='')}"
            f"&start={start}&end={end}&step={step_seconds}s"
        )
        response = self.kubectl("get", "--raw", path, json_output=True)
        if response.get("status") != "success":
            raise RuntimeError(f"Prometheus range query failed: {query}")
        return response

    @staticmethod
    def _matrix(response: dict) -> list[dict]:
        return [
            {"labels": series.get("metric", {}),
             "values": [[float(ts), float(value)] for ts, value in series.get("values", [])]}
            for series in response.get("data", {}).get("result", [])
        ]

    def service_raw(self, namespace: str, service: str, port: int, path: str) -> dict:
        return self.kubectl(
            "get", "--raw", f"/api/v1/namespaces/{namespace}/services/http:{service}:{port}/proxy{path}",
            json_output=True,
        )

    @staticmethod
    def scalar(response: dict) -> float | None:
        result = response.get("data", {}).get("result", [])
        if not result:
            return None
        return float(result[0]["value"][1])

    def snapshot(self) -> dict:
        nodes = self.kubectl("get", "nodes", "-o", "json", json_output=True)
        pods = self.kubectl("-n", self.namespace, "get", "pods", "-o", "json", json_output=True)
        workload_pods = []
        for pod in pods.get("items", []):
            statuses = pod.get("status", {}).get("containerStatuses", [])
            workload_pods.append({
                "name": pod["metadata"]["name"],
                "node": pod.get("spec", {}).get("nodeName"),
                "phase": pod.get("status", {}).get("phase"),
                "ready": bool(statuses) and all(status.get("ready", False) for status in statuses),
                "restarts": sum(status.get("restartCount", 0) for status in statuses),
                "images": [status.get("imageID") for status in statuses],
            })
        memory = self.prometheus_query("node_memory_MemAvailable_bytes")
        sync = self.prometheus_query("node_timex_sync_status")
        scrape = self.prometheus_query(f'count(up{{namespace="{self.namespace}"}} == 1)')
        request_count = self.prometheus_query(
            f'sum(http_server_requests_seconds_count{{namespace="{self.namespace}",uri=~"/api/v1/.*"}})'
        )
        return {
            "nodes": [{
                "name": item["metadata"]["name"],
                "kernel": item.get("status", {}).get("nodeInfo", {}).get("kernelVersion"),
                "kubelet": item.get("status", {}).get("nodeInfo", {}).get("kubeletVersion"),
                "containerRuntime": item.get("status", {}).get("nodeInfo", {}).get("containerRuntimeVersion"),
                "capacity": item.get("status", {}).get("capacity", {}),
                "allocatable": item.get("status", {}).get("allocatable", {}),
            } for item in nodes.get("items", [])],
            "pods": workload_pods,
            "prometheus": {
                "healthyScrapeTargets": self.scalar(scrape),
                "requestCount": self.scalar(request_count),
                "nodeMemoryAvailable": self._vector(memory),
                "nodeTimeSynchronized": self._vector(sync),
            },
        }

    @staticmethod
    def _vector(response: dict) -> list[dict]:
        return [{"labels": item.get("metric", {}), "value": float(item["value"][1])}
                for item in response.get("data", {}).get("result", [])]

    def gate(self, snapshot: dict, require_zero_restarts: bool = False) -> list[str]:
        factors: list[str] = []
        pods = self._measurement_pods(snapshot)
        if not pods or any(not pod["ready"] or pod["phase"] != "Running" for pod in pods):
            factors.append("WORKLOAD_NOT_READY")
        if require_zero_restarts and any(pod["restarts"] != 0 for pod in pods):
            factors.append("WORKLOAD_RESTARTS_NONZERO")
        expected_targets = int(self.config.get("expectedScrapeTargets", 7))
        if (snapshot["prometheus"]["healthyScrapeTargets"] or 0) < expected_targets:
            factors.append("PROMETHEUS_TARGET_GAP")
        minimum_memory = int(self.config.get("minimumNodeMemoryAvailableBytes", 1_073_741_824))
        memory = snapshot["prometheus"]["nodeMemoryAvailable"]
        if not memory or any(item["value"] < minimum_memory for item in memory):
            factors.append("NODE_MEMORY_HEADROOM_LOW")
        sync = snapshot["prometheus"]["nodeTimeSynchronized"]
        if len(sync) < len(snapshot["nodes"]) or any(item["value"] != 1 for item in sync):
            factors.append("NODE_TIME_NOT_SYNCHRONIZED")
        return factors

    def _measurement_pods(self, snapshot: dict) -> list[dict]:
        pods = snapshot.get("pods", [])
        if self.spec.get("scenario") != "SYNC_CHAIN":
            return pods
        return [
            pod for pod in pods
            if pod.get("name", "").startswith(self.SYNC_CHAIN_POD_PREFIXES)
        ]

    def restart_delta_gate(self, before: dict, after: dict) -> list[str]:
        before_restarts = {
            pod["name"]: pod["restarts"] for pod in self._measurement_pods(before)
        }
        increased = [
            pod["name"] for pod in after.get("pods", [])
            if pod in self._measurement_pods(after)
            and pod["restarts"] > before_restarts.get(pod["name"], 0)
        ]
        return ["WORKLOAD_RESTARTS_INCREASED"] if increased else []

    def cleanup_gate(self) -> list[str]:
        pods = self.kubectl(
            "-n", self.namespace, "get", "pods", "-l", "meshperf.io/temporary=true", "-o", "json",
            json_output=True,
        )
        jobs = self.kubectl(
            "-n", self.namespace, "get", "jobs", "-l", "meshperf.io/temporary=true", "-o", "json",
            json_output=True,
        )
        factors = []
        if pods.get("items") or jobs.get("items"):
            factors.append("TEMPORARY_RESOURCES_REMAIN")
        if self.spec.get("faultSchedule"):
            factors.append("FAULT_CLEANUP_UNVERIFIED")
        return factors

    def window_snapshot(self, seconds: int) -> dict:
        window = f"{max(15, seconds)}s"
        return {
            "windowSeconds": max(15, seconds),
            "requestIncrease": self.scalar(self.prometheus_query(
                f'sum(increase(http_server_requests_seconds_count{{namespace="{self.namespace}",'
                f'uri=~"/api/v1/.*"}}[{window}]))'
            )),
            "scrapeMinimum": self._vector(self.prometheus_query(
                f'min_over_time(up{{namespace="{self.namespace}"}}[{window}])'
            )),
            "nodeMemoryMinimum": self._vector(self.prometheus_query(
                f'min_over_time(node_memory_MemAvailable_bytes[{window}])'
            )),
            "collectorFailedSpans": self.scalar(self.prometheus_query(
                f'sum(increase(otelcol_receiver_failed_spans[{window}]))'
            )),
            "collectorRefusedSpans": self.scalar(self.prometheus_query(
                f'sum(increase(otelcol_receiver_refused_spans[{window}]))'
            )),
            "applicationCpuCoreSeconds": self.scalar(self.prometheus_query(
                f'sum(increase(container_cpu_usage_seconds_total{{namespace="{self.namespace}",container!="",'
                f'container!="POD",container!="istio-proxy",container!="istio-init"}}[{window}]))'
            )),
            "applicationCpuPeakCores": self.scalar(self.prometheus_query(
                f'max_over_time((sum(rate(container_cpu_usage_seconds_total{{namespace="{self.namespace}",'
                f'container!="",container!="POD",container!="istio-proxy",container!="istio-init"}}[30s])))[{window}:15s])'
            )),
            "applicationMemoryPeakBytes": self.scalar(self.prometheus_query(
                f'max_over_time((sum(container_memory_working_set_bytes{{namespace="{self.namespace}",'
                f'container!="",container!="POD",container!="istio-proxy",container!="istio-init"}}))[{window}:15s])'
            )),
            "sidecarCpuCoreSeconds": self.scalar(self.prometheus_query(
                f'sum(increase(container_cpu_usage_seconds_total{{namespace="{self.namespace}",'
                f'container="istio-proxy"}}[{window}]))'
            )),
            "sidecarCpuPeakCores": self.scalar(self.prometheus_query(
                f'max_over_time((sum(rate(container_cpu_usage_seconds_total{{namespace="{self.namespace}",'
                f'container="istio-proxy"}}[30s])))[{window}:15s])'
            )),
            "sidecarMemoryPeakBytes": self.scalar(self.prometheus_query(
                f'max_over_time((sum(container_memory_working_set_bytes{{namespace="{self.namespace}",'
                f'container="istio-proxy"}}))[{window}:15s])'
            )),
            "sidecarCpuThrottledPeriods": self.scalar(self.prometheus_query(
                f'sum(increase(container_cpu_cfs_throttled_periods_total{{namespace="{self.namespace}",'
                f'container="istio-proxy"}}[{window}]))'
            )),
            # ztunnel is a per-node DaemonSet shared by every ambient-enrolled pod on
            # that node, not a per-pod sidecar. These are cluster-wide totals across
            # all ztunnel instances during the window, not a value attributable to
            # this experiment alone (see ADR-0025).
            "ztunnelCpuCoreSeconds": self.scalar(self.prometheus_query(
                f'sum(increase(container_cpu_usage_seconds_total{{namespace="istio-system",'
                f'pod=~"ztunnel-.*",container="istio-proxy"}}[{window}]))'
            )),
            "ztunnelCpuPeakCores": self.scalar(self.prometheus_query(
                f'max_over_time((sum(rate(container_cpu_usage_seconds_total{{namespace="istio-system",'
                f'pod=~"ztunnel-.*",container="istio-proxy"}}[30s])))[{window}:15s])'
            )),
            "ztunnelMemoryPeakBytes": self.scalar(self.prometheus_query(
                f'max_over_time((sum(container_memory_working_set_bytes{{namespace="istio-system",'
                f'pod=~"ztunnel-.*",container="istio-proxy"}}))[{window}:15s])'
            )),
            "ztunnelCpuThrottledPeriods": self.scalar(self.prometheus_query(
                f'sum(increase(container_cpu_cfs_throttled_periods_total{{namespace="istio-system",'
                f'pod=~"ztunnel-.*",container="istio-proxy"}}[{window}]))'
            )),
            "networkRxBytes": self.scalar(self.prometheus_query(
                f'sum(increase(container_network_receive_bytes_total{{namespace="{self.namespace}"}}[{window}]))'
            )),
            "networkTxBytes": self.scalar(self.prometheus_query(
                f'sum(increase(container_network_transmit_bytes_total{{namespace="{self.namespace}"}}[{window}]))'
            )),
            "nodeCpuPeakPercent": self.scalar(self.prometheus_query(
                f'max_over_time((100 * (1 - avg(rate(node_cpu_seconds_total{{mode="idle"}}[2m]))))'
                f'[{window}:15s])'
            )),
        }

    def window_gate(self, snapshot: dict) -> list[str]:
        factors = []
        expected_targets = int(self.config.get("expectedScrapeTargets", 7))
        scrape = snapshot["scrapeMinimum"]
        if len(scrape) < expected_targets or any(item["value"] < 1 for item in scrape):
            factors.append("PROMETHEUS_SCRAPE_GAP")
        if (snapshot["requestIncrease"] or 0) <= 0:
            factors.append("PROMETHEUS_REQUEST_DELTA_MISSING")
        minimum_memory = int(self.config.get("minimumNodeMemoryAvailableBytes", 1_073_741_824))
        memory = snapshot["nodeMemoryMinimum"]
        if not memory or any(item["value"] < minimum_memory for item in memory):
            factors.append("NODE_MEMORY_HEADROOM_LOW")
        if (snapshot["collectorFailedSpans"] or 0) > 0:
            factors.append("OTEL_EXPORT_FAILED")
        if (snapshot["collectorRefusedSpans"] or 0) > 0:
            factors.append("OTEL_SPANS_REFUSED")
        if snapshot["nodeCpuPeakPercent"] is None:
            factors.append("NODE_CPU_HEADROOM_MISSING")
        elif snapshot["nodeCpuPeakPercent"] >= float(self.config.get("maximumNodeCpuPercent", 85)):
            factors.append("NODE_CPU_HEADROOM_LOW")
        if (snapshot.get("sidecarCpuThrottledPeriods") or 0) > 0:
            factors.append("PROXY_CPU_THROTTLED")
        if (snapshot.get("ztunnelCpuThrottledPeriods") or 0) > 0:
            factors.append("ZTUNNEL_CPU_THROTTLED")
        return factors

    def window_timeseries(self, start_iso: str, end_iso: str, step_seconds: int = 15) -> dict:
        """Real query_range time series for the run window, saved alongside the
        whole-window aggregate scalars in window_snapshot(). The aggregate-only
        snapshot cannot answer "did this spike during a specific sub-interval"
        (see Phase 8's 2026-07-30 comparison Evidence, "Time-axis correlation"
        section) -- this exists so future runs don't hit that same wall."""
        from datetime import datetime
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00")).timestamp()
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00")).timestamp()
        return {
            "startEpoch": start,
            "endEpoch": end,
            "stepSeconds": step_seconds,
            "applicationCpuCoreRate": self._matrix(self.prometheus_query_range(
                f'sum(rate(container_cpu_usage_seconds_total{{namespace="{self.namespace}",container!="",'
                f'container!="POD",container!="istio-proxy",container!="istio-init"}}[30s]))',
                start, end, step_seconds)),
            "applicationMemoryWorkingSetBytes": self._matrix(self.prometheus_query_range(
                f'sum(container_memory_working_set_bytes{{namespace="{self.namespace}",container!="",'
                f'container!="POD",container!="istio-proxy",container!="istio-init"}})',
                start, end, step_seconds)),
            "sidecarCpuCoreRate": self._matrix(self.prometheus_query_range(
                f'sum(rate(container_cpu_usage_seconds_total{{namespace="{self.namespace}",'
                f'container="istio-proxy"}}[30s]))',
                start, end, step_seconds)),
            "sidecarMemoryWorkingSetBytes": self._matrix(self.prometheus_query_range(
                f'sum(container_memory_working_set_bytes{{namespace="{self.namespace}",container="istio-proxy"}})',
                start, end, step_seconds)),
            "ztunnelCpuCoreRate": self._matrix(self.prometheus_query_range(
                f'sum(rate(container_cpu_usage_seconds_total{{namespace="istio-system",'
                f'pod=~"ztunnel-.*",container="istio-proxy"}}[30s]))',
                start, end, step_seconds)),
            "networkRxBytesRate": self._matrix(self.prometheus_query_range(
                f'sum(rate(container_network_receive_bytes_total{{namespace="{self.namespace}"}}[30s]))',
                start, end, step_seconds)),
            "networkTxBytesRate": self._matrix(self.prometheus_query_range(
                f'sum(rate(container_network_transmit_bytes_total{{namespace="{self.namespace}"}}[30s]))',
                start, end, step_seconds)),
            "nodeCpuPercent": self._matrix(self.prometheus_query_range(
                '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[2m])))',
                start, end, step_seconds)),
            "requestRatePerSecond": self._matrix(self.prometheus_query_range(
                f'sum(rate(http_server_requests_seconds_count{{namespace="{self.namespace}",'
                f'uri=~"/api/v1/.*"}}[30s]))',
                start, end, step_seconds)),
        }

    def trace_marker(self, run_id: str) -> dict:
        request = Request(
            self.spec["targetUrl"].rstrip("/") + "/api/v1/system/ping",
            headers={"X-Experiment-Run-Id": run_id, "X-Correlation-Id": f"{run_id}-trace-marker"},
        )
        with urlopen(request, timeout=10) as response:
            marker = json.loads(response.read())
        trace_id = marker.get("traceId")
        if not trace_id:
            raise RuntimeError("trace marker response has no traceId")
        marker["tempo"] = self._poll_service(
            "observability", "tempo", 3200, f"/api/traces/{trace_id}", attempts=6
        )
        return marker

    def log_marker(self, run_id: str) -> dict:
        name = ("meshperf-log-marker-" + run_id.lower())[:63].rstrip("-")
        image = self.config.get(
            "markerImage",
            "ghcr.io/0206pdh/meshperf-benchmark-gateway@sha256:4fe89712f7a901a39e58911d1e676f57ac521fa0bf7fb4762538ae027a6763cb",
        )
        marker = f"MESHPERF_RUN_MARKER {run_id}"
        try:
            self.kubectl(
                "-n", self.namespace, "run", name, f"--image={image}", "--restart=Never",
                "--labels=meshperf.io/temporary=true", "--command", "--", "/bin/sh", "-c",
                f"echo '{marker}'; sleep 5",
            )
            self.kubectl("-n", self.namespace, "wait", "--for=condition=Ready", f"pod/{name}", "--timeout=60s")
            query = quote(f'{{k8s_namespace_name="{self.namespace}"}} |= "{marker}"', safe="")
            result = None
            for _ in range(8):
                time.sleep(3)
                result = self.service_raw(
                    "observability", "loki", 3100,
                    f"/loki/api/v1/query_range?query={query}&limit=20&since=5m",
                )
                if result.get("data", {}).get("result"):
                    return result
            return result or {}
        finally:
            try:
                self.kubectl("-n", self.namespace, "delete", "pod", name, "--ignore-not-found", "--wait=true")
            except RuntimeError:
                pass

    def hubble_flows(self, seconds: int) -> list[dict]:
        hubble = self.config.get("hubbleBinary") or os.getenv("MESHPERF_HUBBLE")
        if not hubble:
            raise RuntimeError("MESHPERF_HUBBLE or kubernetes.hubbleBinary is required")
        command = ["kubectl"]
        if self.kubeconfig:
            command += ["--kubeconfig", self.kubeconfig]
        command += ["-n", "kube-system", "port-forward", "svc/hubble-relay", "4245:80"]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        forward = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=creationflags)
        try:
            time.sleep(2)
            result = subprocess.run(
                [hubble, "observe", "--server", "localhost:4245", "--namespace", self.namespace,
                 "--since", f"{max(30, seconds)}s", "-o", "json"],
                cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"hubble observe failed: {result.stderr.strip()}")
            return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        finally:
            forward.terminate()
            try:
                forward.wait(timeout=5)
            except subprocess.TimeoutExpired:
                forward.kill()

    def telemetry_gate(self, trace: dict, logs: dict, flows: list[dict]) -> list[str]:
        factors = []
        if not trace.get("tempo", {}).get("batches"):
            factors.append("TEMPO_TRACE_MISSING")
        if not logs.get("data", {}).get("result"):
            factors.append("LOKI_RUN_MARKER_MISSING")
        benchmark_flows = [item for item in flows if item.get("flow", {}).get("verdict") == "FORWARDED"]
        if not benchmark_flows:
            factors.append("HUBBLE_FLOW_MISSING")
        return factors

    def _poll_service(self, namespace: str, service: str, port: int, path: str, attempts: int) -> dict:
        last = {}
        for _ in range(attempts):
            try:
                last = self.service_raw(namespace, service, port, path)
                if last:
                    return last
            except RuntimeError:
                pass
            time.sleep(3)
        return last
