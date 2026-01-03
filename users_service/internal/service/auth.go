package service

import (
    "context"
    "database/sql"
    "fmt"
    "golang.org/x/crypto/bcrypt"
    pb "users_service/pb"
)

func (s *UserServer) AuthenticateUser(ctx context.Context, req *pb.AuthRequest) (*pb.AuthResponse, error) {
    var id int32
    var name, hashedPassword, tipoStr string

    query := `SELECT id, nome, senha, tipo FROM usuario WHERE email = $1`
    err := s.DB.QueryRow(query, req.Email).Scan(&id, &name, &hashedPassword, &tipoStr)
    
    if err == sql.ErrNoRows {
        return nil, fmt.Errorf("Email ou senha inválidos")
    } else if err != nil {
        return nil, fmt.Errorf("erro interno no servidor: %v", err)
    }

    // Compara as senhas, uma "hasheada" e a outra em texto claro.
    err = bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(req.Password))
    if err != nil {
        return nil, fmt.Errorf("Email ou senha inválidos")
    }

    return &pb.AuthResponse{
        Token:    id,
        UserId:   id,
        Name: name,
        UserType: stringToRole(tipoStr),
    }, nil
}