package edu.lus.research.cpu_io_benchmark_api.configuration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@Configuration
@EnableAsync
public class AsyncConfiguration {
    @Bean("cpuBoundExecutor")
    public ThreadPoolTaskExecutor cpuBoundExecutor() {
        ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
        ex.setCorePoolSize(8);
        ex.setMaxPoolSize(8);
        ex.setQueueCapacity(1000);
        ex.setThreadNamePrefix("cpu-");
        return ex;
    }
}