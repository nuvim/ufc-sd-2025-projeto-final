package service

import (
    "database/sql"
    "fmt"
    pb "users_service/pb"
)

type UserServer struct {
    pb.UnimplementedUserServiceServer
    DB *sql.DB
}

func NewUserService(db *sql.DB) *UserServer {
    return &UserServer{DB: db}
}

// Função auxiliar para identificar role do requisitante através do token.
func (s *UserServer) getRequesterRole(token int32) (pb.UserType, error) {
	if token == 0 {
        return pb.UserType_UNKNOWN_ROLE, fmt.Errorf("acesso negado: login obrigatório.")
    }

    var roleStr string
    query := `SELECT tipo FROM usuario WHERE id = $1`
    err := s.DB.QueryRow(query, token).Scan(&roleStr)
    if err != nil {
        return pb.UserType_UNKNOWN_ROLE, fmt.Errorf("usuário solicitante (ID %d) não encontrado", token)
    }

    return stringToRole(roleStr), nil
}

// Função auxiliar para converter string do banco para ENUM do proto.
func stringToRole(roleStr string) pb.UserType {
    switch roleStr {
    case "ADMINISTRADOR":
        return pb.UserType_ADMINISTRADOR
    case "MEDICO":
        return pb.UserType_MEDICO
    case "RECEPCIONISTA":
        return pb.UserType_RECEPCIONISTA
    case "PACIENTE":
        return pb.UserType_PACIENTE
    default:
        return pb.UserType_UNKNOWN_ROLE
    }
}