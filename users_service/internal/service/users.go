package service

import (
	"context"
	"database/sql"
	"fmt"
	"golang.org/x/crypto/bcrypt"
	pb "users_service/pb"
)

type UserServer struct {
	pb.UnimplementedUserServiceServer
	DB *sql.DB
}

func NewUserService(db *sql.DB) *UserServer {
	return &UserServer{DB: db}
}

func (s *UserServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.UserResponse, error) {
	// Verifica a role do requisitante através do token.
	requesterRole, err := s.getRequesterRole(req.Token)
    if err != nil {
        return nil, err
    }

	// Verifica se requisitante possui autorização para criar o usuário. 
	allowed := false
	targetRole := req.UserType
    switch requesterRole {
    case pb.UserType_ADMINISTRADOR:
        // Admin pode criar médico e recepcionista
        if targetRole == pb.UserType_MEDICO || targetRole == pb.UserType_RECEPCIONISTA {
            allowed = true
        }

    case pb.UserType_RECEPCIONISTA:
        // Recepcionista pode criar paciente
        if targetRole == pb.UserType_PACIENTE {
            allowed = true
        }
    }

	if !allowed {
        return nil, fmt.Errorf("permissão negada: %s não pode criar %s", requesterRole, targetRole)
    }

	// Verifica se todos os campos foram preenchidos.
    if req.Name == "" || req.Email == "" || req.Password == "" {
        return nil, fmt.Errorf("erro: todos os campos são obrigatórios")
    }

	// Verifica se já existe um usuário com o email do request.
	var emailExists bool
    queryCheck := `SELECT EXISTS(SELECT 1 FROM usuario WHERE email = $1)`
    err = s.DB.QueryRow(queryCheck, req.Email).Scan(&emailExists)
    if err != nil {
        return nil, fmt.Errorf("erro ao verificar email no banco: %v", err)
    }

    if emailExists {
        return nil, fmt.Errorf("erro: o email '%s' já está cadastrado", req.Email)
    }
	
	// Usa bcrypt para criar o hash da senha.
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("erro ao gerar hash da senha: %v", err)
	}

	// Insere usuário no banco de dados.
	var userID int32
    tipoStr := req.UserType.String()
	query := `INSERT INTO usuario (nome, email, senha, tipo) VALUES ($1, $2, $3, $4) RETURNING id`
	err = s.DB.QueryRow(query, req.Name, req.Email, string(hashedPassword), tipoStr).Scan(&userID)
	if err != nil {
		return nil, fmt.Errorf("erro ao salvar no banco: %v", err)
	}

	// Retorna informações do novo usuário.
	return &pb.UserResponse{
		UserId:   userID,
		Name:     req.Name,
		Email:    req.Email,
		UserType: req.UserType,
	}, nil
}

// Função auxiliar para identificar role do requisitante através do token.
func (s *UserServer) getRequesterRole(token int32) (pb.UserType, error) {
	if token == 0 {
        return pb.UserType_UNKNOWN_ROLE, fmt.Errorf("acesso negado: login obrigatório.")
    }

    var roleStr string
    query := `SELECT tipo FROM usuario WHERE id = $1`
    err = s.DB.QueryRow(query, token).Scan(&roleStr)
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