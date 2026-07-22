package io.meshperf.orchestrator;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

@RestController @RequestMapping("/api/v1/workloads")
class ChainController {
    static final String DEADLINE="X-Request-Deadline-Epoch-Ms"; private final RestClient first;
    ChainController(RestClient.Builder builder,@Value("${mesh-perf.workload.base-url}")String baseUrl){first=builder.baseUrl(baseUrl).build();}
    record Work(@Min(0)@Max(60000)long delayMs,@NotNull String delayDistribution,double errorRate,@Min(0)@Max(10000)long cpuMillis,@Min(0)@Max(67108864)int memoryBytes,@Min(0)@Max(10000)long blockingIoMs,long seed){}
    record Request(@Min(0)@Max(16)int hopCount,@Min(0)@Max(10485760)int payloadBytes,@NotNull@Valid Work work){}
    @PostMapping("/chain") ResponseEntity<Map> chain(@Valid@RequestBody Request body,HttpServletRequest incoming){
        var deadline=incoming.getHeader(DEADLINE);if(deadline!=null&&System.currentTimeMillis()>=Long.parseLong(deadline))return ResponseEntity.status(504).body(Map.of("status","DEADLINE_EXCEEDED","completedHops",0,"elapsedMs",0,"checksum","none"));
        if(body.hopCount()==0)return ResponseEntity.ok(Map.of("status","COMPLETED","completedHops",0,"elapsedMs",0,"checksum","none"));
        var started=System.nanoTime();var call=first.post().uri("/internal/v1/chain-hop").header(CorrelationIdFilter.HEADER,incoming.getHeader(CorrelationIdFilter.HEADER)).header(CorrelationIdFilter.RUN_HEADER,incoming.getHeader(CorrelationIdFilter.RUN_HEADER));
        if(deadline!=null)call.header(DEADLINE,deadline);
        var hop=Map.of("remainingHops",body.hopCount,"completedHops",0,"payloadBytes",body.payloadBytes,"work",body.work);
        try{var result=call.body(hop).retrieve().body(Map.class);result.put("elapsedMs",(System.nanoTime()-started)/1_000_000.0);return ResponseEntity.ok(result);}catch(org.springframework.web.client.HttpServerErrorException.GatewayTimeout error){return ResponseEntity.status(504).body(Map.of("status","DEADLINE_EXCEEDED","completedHops",0,"elapsedMs",(System.nanoTime()-started)/1_000_000.0,"checksum","none"));}
    }
}
