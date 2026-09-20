package edu.lus.research.cpu_io_benchmark_api.DTO;

import java.math.BigDecimal;

public record ProductResponse(Long id, String name, String category, BigDecimal price) {
}
