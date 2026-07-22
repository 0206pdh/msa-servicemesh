package io.meshperf.gateway;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test; import org.springframework.mock.web.*;
import static org.assertj.core.api.Assertions.assertThat;
class BenchmarkGatewayApplicationTests {
 @Test void preservesValidRequestContext(){var f=new CorrelationIdFilter(new SimpleMeterRegistry());var q=new MockHttpServletRequest();q.addHeader(CorrelationIdFilter.HEADER,"cor-1");q.addHeader(CorrelationIdFilter.RUN_HEADER,"run-1");var r=new MockHttpServletResponse();try{f.doFilter(q,r,new MockFilterChain());}catch(Exception e){throw new AssertionError(e);}assertThat(r.getHeader(CorrelationIdFilter.HEADER)).isEqualTo("cor-1");assertThat(r.getHeader(CorrelationIdFilter.RUN_HEADER)).isEqualTo("run-1");}
 @Test void rejectsInvalidRunId(){var f=new CorrelationIdFilter(new SimpleMeterRegistry());var q=new MockHttpServletRequest();q.addHeader(CorrelationIdFilter.RUN_HEADER,"bad run");var r=new MockHttpServletResponse();try{f.doFilter(q,r,new MockFilterChain());}catch(Exception e){throw new AssertionError(e);}assertThat(r.getStatus()).isEqualTo(400);}
}
