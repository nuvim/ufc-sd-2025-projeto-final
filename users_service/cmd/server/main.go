package main

import (
	"log"
	"net"
	"os"

	"google.golang.org/grpc"

	"users_service/internal/database"
	"users_service/internal/service"
	pb "users_service/pb"
)

func main() {
	// Conecta ao banco de dados.
	db, err := database.NewConnection()
	if err != nil {
		log.Fatalf("Erro ao conectar no banco: %v", err)
	}
	defer db.Close() // Garante que a conexão seja fechada quando o programa morrer.

	// Configura a porta do gRPC.
	grpcPort := os.Getenv("GRPC_PORT")
	lis, err := net.Listen("tcp", ":"+grpcPort)
	if err != nil {
		log.Fatalf("Falha ao abrir porta %s: %v", grpcPort, err)
	}

	// Inicializa servidor gRPC.
	grpcServer := grpc.NewServer()
	userService := service.NewUserService(db)
	pb.RegisterUserServiceServer(grpcServer, userService)
	log.Printf("Servidor gRPC escutando na porta %s", grpcPort)

	// Escuta as requisições em um loop infinito.
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Falha ao servir gRPC: %v", err)
	}
}