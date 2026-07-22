package io.meshperf.orchestrator;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry; import org.junit.jupiter.api.Test; import org.springframework.mock.web.*; import static org.assertj.core.api.Assertions.assertThat;
class OrchestratorApplicationTests {@Test void generatesCorrelationId(){var f=new CorrelationIdFilter(new SimpleMeterRegistry());var r=new MockHttpServletResponse();try{f.doFilter(new MockHttpServletRequest(),r,new MockFilterChain());}catch(Exception e){throw new AssertionError(e);}assertThat(r.getHeader(CorrelationIdFilter.HEADER)).isNotBlank();}}
