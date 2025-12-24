package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	_ "github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
	"google.golang.org/grpc"
	pb "github.com/nuvim/ufc-sd-2025-projeto-final/tree/main/users_service"
)

type server struct {
	pb.UnimplementedUserServiceServer
	db *sql.DB
}

func main() {
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbUser := getEnv("DB_USER", "postgres")
	dbPass := getEnv("DB_PASSWORD", "postgres")
	dbName := getEnv("DB_NAME", "medical_system")
	grpcPort := getEnv("GRPC_PORT", "50051")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPass, dbName)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}

	if err := initDatabase(db); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}

	lis, err := net.Listen("tcp", ":"+grpcPort)
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterUserServiceServer(s, &server{db: db})

	log.Printf("gRPC server listening on port %s", grpcPort)
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}

func initDatabase(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS users (
		id SERIAL PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		email VARCHAR(255) UNIQUE NOT NULL,
		password_hash VARCHAR(255) NOT NULL,
		user_type VARCHAR(50) NOT NULL,
		cpf VARCHAR(14) UNIQUE,
		phone VARCHAR(20),
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
	CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);
	`
	_, err := db.Exec(query)
	return err
}

func (s *server) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.UserResponse, error) {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return &pb.UserResponse{
			Success: false,
			Message: "Failed to hash password",
		}, nil
	}

	var userID int32
	var createdAt time.Time
	err = s.db.QueryRow(`
		INSERT INTO users (name, email, password_hash, user_type, cpf, phone)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id, created_at
	`, req.Name, req.Email, string(hashedPassword), req.UserType, req.Cpf, req.Phone).Scan(&userID, &createdAt)

	if err != nil {
		return &pb.UserResponse{
			Success: false,
			Message: fmt.Sprintf("Failed to create user: %v", err),
		}, nil
	}

	return &pb.UserResponse{
		UserId:    userID,
		Name:      req.Name,
		Email:     req.Email,
		UserType:  req.UserType,
		Cpf:       req.Cpf,
		Phone:     req.Phone,
		CreatedAt: createdAt.Format(time.RFC3339),
		Success:   true,
		Message:   "User created successfully",
	}, nil
}

func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.UserResponse, error) {
	var user pb.UserResponse
	var createdAt time.Time

	err := s.db.QueryRow(`
		SELECT id, name, email, user_type, cpf, phone, created_at
		FROM users WHERE id = $1
	`, req.UserId).Scan(&user.UserId, &user.Name, &user.Email, &user.UserType, &user.Cpf, &user.Phone, &createdAt)

	if err != nil {
		if err == sql.ErrNoRows {
			return &pb.UserResponse{
				Success: false,
				Message: "User not found",
			}, nil
		}
		return &pb.UserResponse{
			Success: false,
			Message: fmt.Sprintf("Failed to get user: %v", err),
		}, nil
	}

	user.CreatedAt = createdAt.Format(time.RFC3339)
	user.Success = true
	user.Message = "User retrieved successfully"

	return &user, nil
}

func (s *server) UpdateUser(ctx context.Context, req *pb.UpdateUserRequest) (*pb.UserResponse, error) {
	result, err := s.db.Exec(`
		UPDATE users
		SET name = $1, email = $2, user_type = $3, phone = $4, updated_at = CURRENT_TIMESTAMP
		WHERE id = $5
	`, req.Name, req.Email, req.UserType, req.Phone, req.UserId)

	if err != nil {
		return &pb.UserResponse{
			Success: false,
			Message: fmt.Sprintf("Failed to update user: %v", err),
		}, nil
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return &pb.UserResponse{
			Success: false,
			Message: "User not found",
		}, nil
	}

	return s.GetUser(ctx, &pb.GetUserRequest{UserId: req.UserId})
}

func (s *server) DeleteUser(ctx context.Context, req *pb.DeleteUserRequest) (*pb.DeleteUserResponse, error) {
	result, err := s.db.Exec("DELETE FROM users WHERE id = $1", req.UserId)
	if err != nil {
		return &pb.DeleteUserResponse{
			Success: false,
			Message: fmt.Sprintf("Failed to delete user: %v", err),
		}, nil
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return &pb.DeleteUserResponse{
			Success: false,
			Message: "User not found",
		}, nil
	}

	return &pb.DeleteUserResponse{
		Success: true,
		Message: "User deleted successfully",
	}, nil
}

func (s *server) ListUsers(ctx context.Context, req *pb.ListUsersRequest) (*pb.ListUsersResponse, error) {
	query := "SELECT id, name, email, user_type, cpf, phone, created_at FROM users"
	args := []interface{}{}
	argCount := 1

	if req.UserType != "" {
		query += fmt.Sprintf(" WHERE user_type = $%d", argCount)
		args = append(args, req.UserType)
		argCount++
	}

	query += " ORDER BY created_at DESC"

	if req.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argCount)
		args = append(args, req.Limit)
		argCount++
	}

	if req.Offset > 0 {
		query += fmt.Sprintf(" OFFSET $%d", argCount)
		args = append(args, req.Offset)
	}

	rows, err := s.db.Query(query, args...)
	if err != nil {
		return &pb.ListUsersResponse{}, err
	}
	defer rows.Close()

	var users []*pb.UserResponse
	for rows.Next() {
		var user pb.UserResponse
		var createdAt time.Time

		err := rows.Scan(&user.UserId, &user.Name, &user.Email, &user.UserType, &user.Cpf, &user.Phone, &createdAt)
		if err != nil {
			continue
		}

		user.CreatedAt = createdAt.Format(time.RFC3339)
		user.Success = true
		users = append(users, &user)
	}

	return &pb.ListUsersResponse{
		Users: users,
		Total: int32(len(users)),
	}, nil
}

func (s *server) AuthenticateUser(ctx context.Context, req *pb.AuthRequest) (*pb.AuthResponse, error) {
	var userID int32
	var userType, passwordHash string

	err := s.db.QueryRow(`
		SELECT id, user_type, password_hash
		FROM users WHERE email = $1
	`, req.Email).Scan(&userID, &userType, &passwordHash)

	if err != nil {
		if err == sql.ErrNoRows {
			return &pb.AuthResponse{
				Success: false,
				Message: "Invalid credentials",
			}, nil
		}
		return &pb.AuthResponse{
			Success: false,
			Message: "Authentication failed",
		}, nil
	}

	err = bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password))
	if err != nil {
		return &pb.AuthResponse{
			Success: false,
			Message: "Invalid credentials",
		}, nil
	}

	token := fmt.Sprintf("token_%d_%d", userID, time.Now().Unix())

	return &pb.AuthResponse{
		Success:  true,
		Message:  "Authentication successful",
		UserId:   userID,
		UserType: userType,
		Token:    token,
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}