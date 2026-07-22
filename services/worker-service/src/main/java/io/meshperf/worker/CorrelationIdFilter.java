package io.meshperf.worker;
import io.micrometer.core.instrument.MeterRegistry;
import jakarta.servlet.*; import jakarta.servlet.http.*; import java.io.IOException; import java.util.UUID; import java.util.regex.Pattern;
import org.slf4j.MDC; import org.springframework.stereotype.Component; import org.springframework.web.filter.OncePerRequestFilter;
@Component class CorrelationIdFilter extends OncePerRequestFilter {
    static final String HEADER="X-Correlation-Id", RUN_HEADER="X-Experiment-Run-Id", MDC_KEY="correlationId", RUN_MDC_KEY="experimentRunId";
    private static final Pattern RUN_ID=Pattern.compile("^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$"); private final MeterRegistry meters;
    CorrelationIdFilter(MeterRegistry meters){this.meters=meters;}
    @Override protected void doFilterInternal(HttpServletRequest req,HttpServletResponse res,FilterChain chain)throws ServletException,IOException{
        var supplied=req.getHeader(HEADER); if(supplied!=null&&(supplied.isBlank()||supplied.length()>100)){res.sendError(400,"invalid X-Correlation-Id");return;}
        var runId=req.getHeader(RUN_HEADER); if(runId!=null&&!RUN_ID.matcher(runId).matches()){res.sendError(400,"invalid X-Experiment-Run-Id");return;}
        var generated=supplied==null; var id=generated?UUID.randomUUID().toString():supplied; res.setHeader(HEADER,id); if(runId!=null)res.setHeader(RUN_HEADER,runId);
        meters.counter("meshperf.request.context","correlation_source",generated?"generated":"supplied","run_id",runId==null?"missing":"present").increment();
        try(var a=MDC.putCloseable(MDC_KEY,id);var b=MDC.putCloseable(RUN_MDC_KEY,runId==null?"none":runId)){chain.doFilter(req,res);}
    }
}
