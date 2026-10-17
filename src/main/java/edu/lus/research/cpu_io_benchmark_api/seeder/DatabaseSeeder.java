package edu.lus.research.cpu_io_benchmark_api.seeder;

import edu.lus.research.cpu_io_benchmark_api.models.Order;
import edu.lus.research.cpu_io_benchmark_api.models.OrderStatus;
import edu.lus.research.cpu_io_benchmark_api.models.Product;
import edu.lus.research.cpu_io_benchmark_api.models.User;
import edu.lus.research.cpu_io_benchmark_api.repositories.OrderRepository;
import edu.lus.research.cpu_io_benchmark_api.repositories.ProductRepository;
import edu.lus.research.cpu_io_benchmark_api.repositories.UserRepository;
import lombok.extern.slf4j.Slf4j;
import net.datafaker.Faker;
import org.jspecify.annotations.NonNull;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Component
public class DatabaseSeeder implements CommandLineRunner {
    private static final long RANDOM_SEED = 42L;
    private static final int PRODUCT_COUNT = 150;
    private static final int MAX_NAME_LENGTH = 50;
    private static final List<String> CATEGORIES = List.of(
            "Electronics", "Books", "Clothing", "Home", "Garden",
            "Toys", "Sports", "Beauty", "Grocery", "Automotive");

    private static final int MAX_NUMBER_OF_USERS = 1000;
    private static final List<Character> PASSWORD_LETTERS = List.of(
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    );
    private static final LocalDateTime USER_DATETIME_ANCHOR = LocalDateTime.of(2025, 1, 1, 0, 0);
    private static final int USER_DATETIME_RANGE_MINUTES = 365 * 24 * 60;

    private static final int INVALID_LOGIN_COUNT = 50;
    private static final String CREDENTIALS_CSV = "db/seeded-users.csv";

    private static final int NUMBER_OF_ORDERS_PER_USER = 40;
    private static final LocalDate ORDER_DATE_ANCHOR = LocalDate.of(2026, 1, 1);
    private static final int ORDER_DATE_RANGE_DAYS = 365;

    private final boolean seedEnabled;
    private final UserRepository userRepository;
    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final PasswordEncoder passwordEncoder;

    public DatabaseSeeder(@Value("${app.seed.enabled:false}") boolean seedEnabled,
                          UserRepository userRepository,
                          OrderRepository orderRepository,
                          ProductRepository productRepository,
                          PasswordEncoder passwordEncoder) {
        this.seedEnabled = seedEnabled;
        this.userRepository = userRepository;
        this.orderRepository = orderRepository;
        this.productRepository = productRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String @NonNull ... args) {
        if (!seedEnabled) {
            log.info("Seeder skipped: app.seed.enabled is false");
            return;
        }

        final long usersCount = userRepository.count();
        final long productsCount = productRepository.count();
        final long ordersCount = orderRepository.count();

        if (usersCount != 0 || productsCount != 0 || ordersCount != 0) {
            throw new IllegalStateException(String.format(
                    "Seeder refused to run: tables are not empty (users=%d, products=%d, orders=%d). "
                            + "Truncate them first.", usersCount, productsCount, ordersCount));
        }

        try {
            Random random = new Random(RANDOM_SEED);
            Faker faker = new Faker(random);

            List<Product> products = seedProducts(random, faker);
            log.info("Seeded {} products", products.size());

            List<User> users = seedUsersAndExportCredentials(random);
            log.info("Seeded {} users", users.size());

            List<Order> orders = seedOrders(random, users, products);
            log.info("Seeded {} orders", orders.size());
        } catch (RuntimeException e) {
            rollback();
            throw new IllegalStateException(
                    "Seeding failed and was rolled back. TRUNCATE orders, users and products "
                            + "before re-running, because deleting rows does not reset auto-increment ids.", e);
        }
    }

    private void rollback() {
        log.error("Seeding failed, rolling back all three tables and the credentials CSV");
        try {
            orderRepository.deleteAllInBatch();
            userRepository.deleteAllInBatch();
            productRepository.deleteAllInBatch();
        } catch (RuntimeException cleanupError) {
            log.error("Rollback of the database tables failed; TRUNCATE them manually", cleanupError);
        }
        try {
            Files.deleteIfExists(Path.of(CREDENTIALS_CSV));
        } catch (IOException cleanupError) {
            log.error("Could not delete {}; remove it manually", CREDENTIALS_CSV, cleanupError);
        }
    }

    private List<Product> seedProducts(Random random, Faker faker) {
        Set<String> names = new LinkedHashSet<>();
        while (names.size() < PRODUCT_COUNT) {
            String name = faker.commerce().productName();
            if (name.length() <= MAX_NAME_LENGTH) {
                names.add(name);
            }
        }

        List<Product> products = new ArrayList<>();
        for (String name : names) {
            Product product = new Product();
            product.setName(name);
            product.setCategory(CATEGORIES.get(random.nextInt(CATEGORIES.size())));
            product.setPrice(BigDecimal.valueOf(500 + random.nextInt(99_500), 2));
            products.add(product);
        }

        return productRepository.saveAll(products);
    }

    private List<User> seedUsersAndExportCredentials(Random random) {
        List<User> users = new ArrayList<>();
        List<String> rawPasswords = new ArrayList<>();

        for (int i = 0; i < MAX_NUMBER_OF_USERS; i++) {
            String rawPassword = randomPassword(random);

            User user = new User();
            user.setUsername(String.format("user%04d", i + 1));
            user.setEmail(String.format("user%04d@example.com", i + 1));
            user.setPasswordHash(passwordEncoder.encode(rawPassword));
            // spread signups across one year: the range is in minutes, so add minutes
            user.setCreationDate(USER_DATETIME_ANCHOR.plusMinutes(random.nextInt(USER_DATETIME_RANGE_MINUTES)));

            users.add(user);
            rawPasswords.add(rawPassword);
        }

        List<User> saved = userRepository.saveAll(users);

        try {
            writeCredentialsCsv(saved, rawPasswords, random);
        } catch (IOException e) {
            throw new IllegalStateException("Could not write " + CREDENTIALS_CSV, e);
        }
        return saved;
    }

    private void writeCredentialsCsv(List<User> saved, List<String> rawPasswords, Random random)
            throws IOException {
        // pick 50 distinct users to receive a wrong password
        List<Integer> indices = new ArrayList<>();
        for (int i = 0; i < saved.size(); i++) indices.add(i);
        Collections.shuffle(indices, random);
        Set<Integer> invalid = new HashSet<>(indices.subList(0, INVALID_LOGIN_COUNT));

        List<String> rows = new ArrayList<>();
        for (int i = 0; i < saved.size(); i++) {
            User user = saved.get(i);
            String password = rawPasswords.get(i);
            int expected = 200;

            if (invalid.contains(i)) {
                String wrong;
                do {
                    wrong = randomPassword(random);
                } while (wrong.equals(password));   // never equal to the real one
                password = wrong;
                expected = 401;
            }
            rows.add(String.join(",", user.getUsername(), password,
                    String.valueOf(expected), String.valueOf(user.getId())));
        }

        Collections.shuffle(rows, random);          // mix valid and invalid rows

        List<String> lines = new ArrayList<>();
        lines.add("username,password,expected,user_id");
        lines.addAll(rows);

        Path csvPath = Path.of(CREDENTIALS_CSV);
        if (csvPath.getParent() != null) {
            Files.createDirectories(csvPath.getParent());
        }
        Files.write(csvPath, lines);
        log.info("Wrote {} credential rows to {}", rows.size(), csvPath.toAbsolutePath());
    }

    private String randomPassword(Random random) {
        int length = 8 + random.nextInt(13); // 8 to 20 inclusive
        StringBuilder password = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            password.append(PASSWORD_LETTERS.get(random.nextInt(PASSWORD_LETTERS.size())));
        }
        return password.toString();
    }

    private List<Order> seedOrders(Random random, List<User> users, List<Product> products) {
        List<Order> orders = new ArrayList<>(users.size() * NUMBER_OF_ORDERS_PER_USER);
        OrderStatus[] statuses = OrderStatus.values();

        for (User user : users) {
            // copy and shuffle: the first 40 are distinct products
            List<Product> shuffled = new ArrayList<>(products);
            Collections.shuffle(shuffled, random);

            for (Product product : shuffled.subList(0, NUMBER_OF_ORDERS_PER_USER)) {
                Order order = new Order();
                order.setUser(user);
                order.setProduct(product);
                order.setStatus(statuses[random.nextInt(statuses.length)]);
                order.setOrderDate(ORDER_DATE_ANCHOR.plusDays(random.nextInt(ORDER_DATE_RANGE_DAYS)));
                orders.add(order);
            }
        }

        List<Order> saved = new ArrayList<>(orders.size());
        // save in chunks of 1,000 so memory stays calm and progress is visible
        for (int from = 0; from < orders.size(); from += 1000) {
            int to = Math.min(from + 1000, orders.size());
            saved.addAll(orderRepository.saveAll(orders.subList(from, to)));
            log.info("Saved {} / {} orders", to, orders.size());
        }
        return saved;
    }
}