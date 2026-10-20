package edu.lus.research.cpu_io_benchmark_api.controller;

import edu.lus.research.cpu_io_benchmark_api.DTO.LoginRequest;
import edu.lus.research.cpu_io_benchmark_api.service.AuthService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public CompletableFuture<ResponseEntity<String>> login(@RequestBody LoginRequest loginRequest) {
        return authService.login(loginRequest).thenApply(ok -> ok
                ? ResponseEntity.ok("User logged in successfully")
                : ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Invalid credentials"));
    }
}
