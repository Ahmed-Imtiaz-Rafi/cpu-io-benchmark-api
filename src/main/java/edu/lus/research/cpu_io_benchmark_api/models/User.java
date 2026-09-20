package edu.lus.research.cpu_io_benchmark_api.models;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;


@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    @Column(unique = true, nullable = false, length = 100)
    String username;
    @Column(unique = true, nullable = false, length = 100)
    String email;
    @Column(nullable = false, length = 60)
    String passwordHash;
    @Column(nullable = false, updatable = false)
    private LocalDateTime creationDate;
    @OneToMany(fetch = FetchType.LAZY, mappedBy = "user")
    Set<Order> orders = new HashSet<>();

    public void addOrder(Order order) {
        orders.add(order);
        order.setUser(this);
    }
}
