package io.meshperf.worker;
import java.nio.charset.StandardCharsets; import java.security.MessageDigest; import java.util.*;
import org.springframework.core.env.Environment; import org.springframework.web.bind.annotation.*;
@RestController @RequestMapping("/internal/v1") class RuntimeConfigController {
    private final Map<String,String> snapshot;
    RuntimeConfigController(Environment env){var v=new TreeMap<String,String>(); v.put("service",env.getRequiredProperty("spring.application.name")); v.put("role","worker"); v.put("javaVersion",Runtime.version().toString()); v.put("imageDigest",env.getProperty("mesh-perf.image-digest","local")); v.put("tracingSamplingProbability",env.getProperty("management.tracing.sampling.probability","1.0")); v.put("topologyTarget",env.getProperty("mesh-perf.kafka.bootstrap-servers","none")); v.put("fingerprint",sha(v.toString())); snapshot=Map.copyOf(v);}
    @GetMapping("/config") Map<String,String> config(){return snapshot;}
    private static String sha(String s){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));}catch(Exception e){throw new IllegalStateException(e);}}
}
