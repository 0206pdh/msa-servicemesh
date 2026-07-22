package io.meshperf.orchestrator;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;

@RestController @RequestMapping("/api/v1/workloads")
class FanoutController {
    private final RestClient target;
    FanoutController(RestClient.Builder builder,@Value("${mesh-perf.workload.base-url}")String baseUrl){target=builder.baseUrl(baseUrl).build();}
    enum Mode{SEQUENTIAL,PARALLEL}
    record Request(@Min(1)@Max(64)int targetCount,@NotNull Mode mode,@Min(1)@Max(60000)long timeoutBudgetMs,Boolean allowPartial,Map<String,Object> work){
        Request { if(allowPartial==null)allowPartial=true;if(work==null)work=Map.of("delayMs",0,"delayDistribution","FIXED","errorRate",0,"cpuMillis",0,"memoryBytes",0,"blockingIoMs",0,"seed",0); }
    }
    record Outcome(String target,String status,double elapsedMs,String errorCode){}
    @PostMapping("/fanout") Map<String,Object> fanout(@Valid@RequestBody Request body,HttpServletRequest incoming){
        var memory=((Number)body.work.getOrDefault("memoryBytes",0)).longValue();if(memory*body.targetCount>268_435_456L)throw new org.springframework.web.server.ResponseStatusException(org.springframework.http.HttpStatus.BAD_REQUEST,"fan-out aggregate memory exceeds 256 MiB safety limit");
        var deadline=System.nanoTime()+body.timeoutBudgetMs*1_000_000L;List<Outcome> outcomes;
        if(body.mode==Mode.SEQUENTIAL){outcomes=new ArrayList<>();for(int i=0;i<body.targetCount;i++)outcomes.add(call(i,deadline,body.work,incoming));}
        else {var executor=Executors.newVirtualThreadPerTaskExecutor();try{var futures=new ArrayList<java.util.concurrent.Future<Outcome>>();for(int i=0;i<body.targetCount;i++){int targetIndex=i;futures.add(executor.submit(()->call(targetIndex,deadline,body.work,incoming)));}outcomes=new ArrayList<>();for(int i=0;i<futures.size();i++){var future=futures.get(i);try{var remaining=Math.max(1,deadline-System.nanoTime());outcomes.add(future.get(remaining,TimeUnit.NANOSECONDS));}catch(Exception e){future.cancel(true);outcomes.add(new Outcome("target-"+i,"TIMED_OUT",0,"BUDGET_EXCEEDED"));}}}finally{executor.shutdownNow();}}
        var completed=outcomes.stream().filter(o->o.status.equals("COMPLETED")).count();var failed=outcomes.size()-completed;var status=failed==0?"COMPLETED":completed>0&&body.allowPartial()?"PARTIAL":"FAILED";
        return Map.of("status",status,"completedTargets",completed,"failedTargets",failed,"outcomes",outcomes);
    }
    private Outcome call(int index,long deadline,Map<String,Object> work,HttpServletRequest incoming){var started=System.nanoTime();if(System.nanoTime()>=deadline)return new Outcome("target-"+index,"TIMED_OUT",0,"BUDGET_EXCEEDED");try{var request=Map.of("work",withSeed(work,index),"responseBytes",0);target.post().uri("/api/v1/workloads/target").header(CorrelationIdFilter.HEADER,incoming.getHeader(CorrelationIdFilter.HEADER)).header(CorrelationIdFilter.RUN_HEADER,incoming.getHeader(CorrelationIdFilter.RUN_HEADER)).body(request).retrieve().toBodilessEntity();return new Outcome("target-"+index,"COMPLETED",(System.nanoTime()-started)/1_000_000.0,null);}catch(Exception e){return new Outcome("target-"+index,"FAILED",(System.nanoTime()-started)/1_000_000.0,"TARGET_ERROR");}}
    private static Map<String,Object> withSeed(Map<String,Object> work,int index){var copy=new HashMap<>(work);var seed=((Number)copy.getOrDefault("seed",0)).longValue();copy.put("seed",seed+index);return copy;}
}
