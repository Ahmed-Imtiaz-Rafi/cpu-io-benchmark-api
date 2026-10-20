package edu.lus.research.cpu_io_benchmark_api.service;

import edu.lus.research.cpu_io_benchmark_api.DTO.LoginRequest;
import edu.lus.research.cpu_io_benchmark_api.models.User;
import edu.lus.research.cpu_io_benchmark_api.repositories.UserRepository;
import org.springframework.scheduling.annotation.Async;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final PasswordEncoder bCryptPasswordEncoder;

    public AuthService(UserRepository userRepository, PasswordEncoder bCryptPasswordEncoder) {
        this.userRepository = userRepository;
        this.bCryptPasswordEncoder = bCryptPasswordEncoder;
    }

    @Async("cpuBoundExecutor")
    public CompletableFuture<Boolean> login(LoginRequest loginRequest) {
        User user = userRepository.findByUsername(loginRequest.username());
        if (user == null) {
            return CompletableFuture.completedFuture(false);
        }
        return CompletableFuture.completedFuture(
                bCryptPasswordEncoder.matches(loginRequest.password(), user.getPasswordHash()));
    }
}
