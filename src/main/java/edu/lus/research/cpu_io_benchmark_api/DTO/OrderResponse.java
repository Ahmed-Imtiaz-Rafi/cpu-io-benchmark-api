package edu.lus.research.cpu_io_benchmark_api.DTO;

import edu.lus.research.cpu_io_benchmark_api.models.OrderStatus;

import java.time.LocalDate;

public record OrderResponse(Long id, ProductResponse product, LocalDate orderDate, OrderStatus orderStatus) {
}
