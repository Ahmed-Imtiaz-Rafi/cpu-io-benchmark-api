package edu.lus.research.cpu_io_benchmark_api.repositories;

import edu.lus.research.cpu_io_benchmark_api.models.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
    User findByUsername(String username);
}
