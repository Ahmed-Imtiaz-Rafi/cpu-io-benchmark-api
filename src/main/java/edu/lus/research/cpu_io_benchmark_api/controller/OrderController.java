package edu.lus.research.cpu_io_benchmark_api.controller;

import edu.lus.research.cpu_io_benchmark_api.DTO.OrderResponse;
import edu.lus.research.cpu_io_benchmark_api.service.OrderService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/users/{userId}/orders")
    public ResponseEntity<List<OrderResponse>> getOrders(@PathVariable Long userId) {
        return ResponseEntity.ok(orderService.findAllOrders(userId));
    }
}
