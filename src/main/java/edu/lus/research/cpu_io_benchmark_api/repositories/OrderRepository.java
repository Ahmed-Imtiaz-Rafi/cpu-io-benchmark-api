package edu.lus.research.cpu_io_benchmark_api.repositories;

import edu.lus.research.cpu_io_benchmark_api.models.Order;
import edu.lus.research.cpu_io_benchmark_api.models.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {
    @Query("SELECT o FROM Order o JOIN FETCH o.product WHERE o.user.id = :userId")
    List<Order> findByUserIdWithProduct(@Param("userid") Long userid);

    Long user(User user);
}
