package edu.lus.research.cpu_io_benchmark_api.service;

import edu.lus.research.cpu_io_benchmark_api.DTO.OrderResponse;
import edu.lus.research.cpu_io_benchmark_api.DTO.ProductResponse;
import edu.lus.research.cpu_io_benchmark_api.models.Order;
import edu.lus.research.cpu_io_benchmark_api.models.Product;
import edu.lus.research.cpu_io_benchmark_api.repositories.OrderRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public List<OrderResponse> findAllOrders(Long userId) {
        List<Order> orders = orderRepository.findByUserIdWithProduct(userId);
        return orders.stream().map(this::orderToOrderResponse).toList();
    }

    private OrderResponse orderToOrderResponse(Order order) {
        return new OrderResponse(
                order.getId(),
                productToProductResponse(order.getProduct()),
                order.getOrderDate(),
                order.getStatus()
        );
    }

    private ProductResponse productToProductResponse(Product product) {
        return new ProductResponse(
                product.getId(),
                product.getName(),
                product.getCategory(),
                product.getPrice()
        );
    }
}
