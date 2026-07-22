package io.meshperf.producer;

import jakarta.validation.Valid; import jakarta.validation.constraints.*; import java.time.Instant; import java.util.*; import java.util.concurrent.CompletableFuture;
import org.slf4j.MDC; import org.springframework.http.HttpStatus; import org.springframework.kafka.core.KafkaTemplate; import org.springframework.web.bind.annotation.*;
import tools.jackson.databind.ObjectMapper;
@RestController @RequestMapping("/api/v1/workloads/async") class TaskProducerController {
 private static final long MAX_BATCH_PAYLOAD_BYTES=67_108_864L;
 private final KafkaTemplate<String,String> kafka; private final ObjectMapper json; TaskProducerController(KafkaTemplate<String,String> kafka,ObjectMapper json){this.kafka=kafka;this.json=json;}
 record Request(@Min(1)@Max(10000)int taskCount,@Min(0)@Max(60000)int processingMillis,@Min(0)@Max(10485760)int payloadBytes,long seed){}
 record Task(String eventId,String experimentRunId,String createdAt,TaskBody task){} record TaskBody(String idempotencyKey,int processingMillis,int payloadBytes,String payloadBase64,long seed){}
 @PostMapping("/tasks") @ResponseStatus(HttpStatus.ACCEPTED) Map<String,Object> publish(@Valid@RequestBody Request request){if((long)request.taskCount*request.payloadBytes>MAX_BATCH_PAYLOAD_BYTES)throw new org.springframework.web.server.ResponseStatusException(HttpStatus.BAD_REQUEST,"batch payload exceeds 64 MiB safety limit");var batch=UUID.randomUUID().toString();var run=Optional.ofNullable(MDC.get(CorrelationIdFilter.RUN_MDC_KEY)).orElse("none");var sends=new ArrayList<CompletableFuture<?>>();for(int i=0;i<request.taskCount;i++){var key=batch+"-"+i;var bytes=new byte[request.payloadBytes];new SplittableRandom(request.seed+i).nextBytes(bytes);var task=new Task(UUID.randomUUID().toString(),run,Instant.now().toString(),new TaskBody(key,request.processingMillis,request.payloadBytes,Base64.getEncoder().encodeToString(bytes),request.seed+i));sends.add(kafka.send("meshperf.tasks.v1",key,json.writeValueAsString(task)));}CompletableFuture.allOf(sends.toArray(CompletableFuture[]::new)).join();return Map.of("batchId",batch,"accepted",request.taskCount,"rejected",0);}
}
