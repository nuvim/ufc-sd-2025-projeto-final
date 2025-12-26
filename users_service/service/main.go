package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	// Drivers e Libs
	_ "github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"
	"google.golang.org/grpc"
	
	// Importa seu pacote local gerado pelo protoc
	pb "users_service/pb"
)

type server struct {
	pb.UnimplementedUserServiceServer
	db *sql.DB
}

func main() {
	// Configurações de conexão
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbUser := getEnv("DB_USER", "user")
	dbPass := getEnv("DB_PASSWORD", "password")
	dbName := getEnv("DB_NAME", "clinica-app") // Atenção ao nome do banco no docker-compose
	grpcPort := getEnv("GRPC_PORT", "50051")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPass, dbName)

	// Conecta no Banco
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatalf("Falha ao abrir driver: %v", err)
	}
	defer db.Close()

	// Testa conexão
	if err := db.Ping(); err != nil {
		log.Fatalf("Falha ao conectar no banco (Ping): %v", err)
	}
	log.Println("Conectado ao Banco de Dados com sucesso!")

	// NÃO rodamos initDatabase aqui. 
	// Deixamos o init.sql do Docker criar as tabelas para evitar conflito de permissões.

	lis, err := net.Listen("tcp", ":"+grpcPort)
	if err != nil {
		log.Fatalf("Falha ao ouvir porta: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterUserServiceServer(s, &server{db: db})

	log.Printf("Servidor gRPC rodando na porta %s", grpcPort)
	if err := s.Serve(lis); err != nil {
		log.Fatalf("Falha ao servir: %v", err)
	}
}

// --- Implementação dos Métodos gRPC ---

func (s *server) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.UserResponse, error) {
	// 1. Criptografa a senha
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("erro ao gerar hash da senha: %v", err)
	}

	var userID int32
	
	// 2. Converte o ENUM do Proto para String do Banco
	// Ex: Enum 4 vira string "PACIENTE"
	userTypeString := req.GetUserType().String()

	// 3. Insere na tabela 'usuario' (do seu init.sql)
	// Removemos CPF e Fone pois eles não existem mais no seu proto/banco
	err = s.db.QueryRow(`
		INSERT INTO usuario (nome, email, senha, tipo)
		VALUES ($1, $2, $3, $4)
		RETURNING id
	`, req.Name, req.Email, string(hashedPassword), userTypeString).Scan(&userID)

	if err != nil {
		log.Printf("Erro SQL: %v", err)
		return nil, fmt.Errorf("erro ao inserir usuário: %v", err)
	}

	return &pb.UserResponse{
		UserId:   userID,
		Name:     req.Name,
		Email:    req.Email,
		UserType: req.UserType, // Devolve o ENUM original
	}, nil
}

func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.UserResponse, error) {
	var user pb.UserResponse
	var tipoString string
	var senhaIgnorada string // Não retornamos a senha hash

	err := s.db.QueryRow(`
		SELECT id, nome, email, tipo, senha
		FROM usuario WHERE id = $1
	`, req.UserId).Scan(&user.UserId, &user.Name, &user.Email, &tipoString, &senhaIgnorada)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("usuário não encontrado")
		}
		return nil, err
	}

	// Mapeia a string do banco de volta para o ENUM do proto seria complexo,
	// mas para simplificar, o UserResponse no proto atual aceita o ENUM.
	// Nota: Se precisar converter String -> Enum, precisaria de um switch case.
	// Por enquanto, retornamos o userType zerado ou fixo se não fizermos o map.
	// user.UserType = ... (Lógica de mapeamento reverso se necessário)

	return &user, nil
}

func (s *server) AuthenticateUser(ctx context.Context, req *pb.AuthRequest) (*pb.AuthResponse, error) {
	var userID int32
	var userTypeString, passwordHash string

	// Busca pelo email
	err := s.db.QueryRow(`
		SELECT id, tipo, senha
		FROM usuario WHERE email = $1
	`, req.Email).Scan(&userID, &userTypeString, &passwordHash)

	if err != nil {
		return &pb.AuthResponse{Success: false, Message: "Usuário não encontrado"}, nil
	}

	// Compara a senha enviada com o Hash do banco
	err = bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(req.Password))
	if err != nil {
		return &pb.AuthResponse{Success: false, Message: "Senha incorreta"}, nil
	}

	// Gera token simples
	token := fmt.Sprintf("token_mock_%d_%d", userID, time.Now().Unix())

	return &pb.AuthResponse{
		Success:  true,
		Message:  "Login realizado!",
		UserId:   userID,
		Token:    token,
		// UserType: ... (teria que converter string->enum aqui também)
	}, nil
}

// Métodos obrigatórios do gRPC que faltavam (Placeholders)
func (s *server) UpdateUser(ctx context.Context, req *pb.UpdateUserRequest) (*pb.UserResponse, error) {
	return &pb.UserResponse{}, nil // Implementar se der tempo
}

func (s *server) DeleteUser(ctx context.Context, req *pb.DeleteUserRequest) (*pb.DeleteUserResponse, error) {
	_, err := s.db.Exec("DELETE FROM usuario WHERE id = $1", req.UserId)
	return &pb.DeleteUserResponse{Success: err == nil}, err
}

func (s *server) ListUsers(ctx context.Context, req *pb.ListUsersRequest) (*pb.ListUsersResponse, error) {
	return &pb.ListUsersResponse{}, nil 
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}