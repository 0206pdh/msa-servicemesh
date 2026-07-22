package io.meshperf.gateway;
import jakarta.servlet.http.HttpServletRequest; import java.util.Map;
import org.springframework.beans.factory.annotation.Value; import org.springframework.http.ResponseEntity; import org.springframework.web.bind.annotation.*; import org.springframework.web.client.RestClient;
@RestController @RequestMapping("/api/v1/workloads") class WorkloadProxyController {
 private static final String DEADLINE="X-Request-Deadline-Epoch-Ms"; private final RestClient orchestrator; private final RestClient producer;
 WorkloadProxyController(RestClient.Builder builder,@Value("${mesh-perf.orchestrator.base-url}")String baseUrl,@Value("${mesh-perf.producer.base-url}")String producerUrl){orchestrator=builder.baseUrl(baseUrl).build();producer=builder.baseUrl(producerUrl).build();}
 @PostMapping("/chain") ResponseEntity<Map> chain(@RequestBody Map<String,Object> body,HttpServletRequest incoming){
  var call=orchestrator.post().uri("/api/v1/workloads/chain").header(CorrelationIdFilter.HEADER,incoming.getHeader(CorrelationIdFilter.HEADER)).header(CorrelationIdFilter.RUN_HEADER,incoming.getHeader(CorrelationIdFilter.RUN_HEADER));
  var deadline=incoming.getHeader(DEADLINE);if(deadline!=null)call.header(DEADLINE,deadline);
  try{return ResponseEntity.ok(call.body(body).retrieve().body(Map.class));}catch(org.springframework.web.client.HttpServerErrorException.GatewayTimeout error){return ResponseEntity.status(504).body((Map)error.getResponseBodyAs(Map.class));}
 }
 @PostMapping("/fanout") ResponseEntity<Map> fanout(@RequestBody Map<String,Object> body,HttpServletRequest incoming){
  return ResponseEntity.ok(orchestrator.post().uri("/api/v1/workloads/fanout").header(CorrelationIdFilter.HEADER,incoming.getHeader(CorrelationIdFilter.HEADER)).header(CorrelationIdFilter.RUN_HEADER,incoming.getHeader(CorrelationIdFilter.RUN_HEADER)).body(body).retrieve().body(Map.class));
 }
 @PostMapping("/payload") ResponseEntity<Map> payload(@RequestBody Map<String,Object> body,HttpServletRequest incoming){
  var call=orchestrator.post().uri("/api/v1/workloads/payload").header(CorrelationIdFilter.HEADER,incoming.getHeader(CorrelationIdFilter.HEADER)).header(CorrelationIdFilter.RUN_HEADER,incoming.getHeader(CorrelationIdFilter.RUN_HEADER));
  var deadline=incoming.getHeader(DEADLINE);if(deadline!=null)call.header(DEADLINE,deadline);
  return ResponseEntity.ok(call.body(body).retrieve().body(Map.class));
 }
 @PostMapping("/async/tasks") ResponseEntity<Map> async(@RequestBody Map<String,Object> body,HttpServletRequest incoming){
  var result=producer.post().uri("/api/v1/workloads/async/tasks").header(CorrelationIdFilter.HEADER,incoming.getHeader(CorrelationIdFilter.HEADER)).header(CorrelationIdFilter.RUN_HEADER,incoming.getHeader(CorrelationIdFilter.RUN_HEADER)).body(body).retrieve().body(Map.class);
  return ResponseEntity.accepted().body(result);
 }
}
