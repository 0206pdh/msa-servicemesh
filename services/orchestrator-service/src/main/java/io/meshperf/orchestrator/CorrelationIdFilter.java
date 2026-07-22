package io.meshperf.orchestrator;

import io.micrometer.core.instrument.MeterRegistry;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
class CorrelationIdFilter extends OncePerRequestFilter {
    static final String HEADER = "X-Correlation-Id";
    static final String RUN_HEADER = "X-Experiment-Run-Id";
    static final String MDC_KEY = "correlationId";
    static final String RUN_MDC_KEY = "experimentRunId";
    private static final Pattern RUN_ID = Pattern.compile("^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$");
    private final MeterRegistry meters;
    CorrelationIdFilter(MeterRegistry meters) { this.meters = meters; }
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain) throws ServletException, IOException {
        var supplied = request.getHeader(HEADER);
        if (supplied != null && (supplied.isBlank() || supplied.length() > 100)) { response.sendError(400, "invalid X-Correlation-Id"); return; }
        var runId = request.getHeader(RUN_HEADER);
        if (runId != null && !RUN_ID.matcher(runId).matches()) { response.sendError(400, "invalid X-Experiment-Run-Id"); return; }
        var generated = supplied == null;
        var id = generated ? UUID.randomUUID().toString() : supplied;
        response.setHeader(HEADER, id); if (runId != null) response.setHeader(RUN_HEADER, runId);
        meters.counter("meshperf.request.context", "correlation_source", generated ? "generated" : "supplied", "run_id", runId == null ? "missing" : "present").increment();
        try (var ignoredId = MDC.putCloseable(MDC_KEY, id); var ignoredRun = MDC.putCloseable(RUN_MDC_KEY, runId == null ? "none" : runId)) { chain.doFilter(request, response); }
    }
}
