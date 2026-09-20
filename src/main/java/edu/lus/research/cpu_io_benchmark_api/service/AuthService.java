package edu.lus.research.cpu_io_benchmark_api.service;

import edu.lus.research.cpu_io_benchmark_api.DTO.LoginRequest;
import edu.lus.research.cpu_io_benchmark_api.models.User;
import edu.lus.research.cpu_io_benchmark_api.repositories.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final PasswordEncoder bCryptPasswordEncoder;

    public AuthService(UserRepository userRepository, PasswordEncoder bCryptPasswordEncoder) {
        this.userRepository = userRepository;
        this.bCryptPasswordEncoder = bCryptPasswordEncoder;
    }

    public boolean login(LoginRequest loginRequest) {
        User user = userRepository.findByUsername(loginRequest.username());
        if (user == null) {
            return false;
        }
        return bCryptPasswordEncoder.matches(loginRequest.password(), user.getPasswordHash());
    }


}
