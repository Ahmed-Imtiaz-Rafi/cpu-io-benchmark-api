package edu.lus.research.cpu_io_benchmark_api.repositories;

import edu.lus.research.cpu_io_benchmark_api.models.Product;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository extends JpaRepository<Product, Long> {
}
