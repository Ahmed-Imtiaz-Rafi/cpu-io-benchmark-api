package edu.lus.research.cpu_io_benchmark_api.configuration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@Configuration
@EnableAsync
public class AsyncConfiguration {
    @Bean("cpuBoundExecutor")
    public ThreadPoolTaskExecutor cpuBoundExecutor(@Value("${app.cpu-executor.size:8}") int size) {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(size);
        ex.setMaxPoolSize(size);
        ex.setQueueCapacity(1000);
        ex.setThreadNamePrefix("cpu-");
        return ex;
    }
}