package service

import (
	"context"
    "database/sql"

	"golang.org/x/crypto/bcrypt"

    "google.golang.org/grpc/status"
    "google.golang.org/grpc/codes"
    "google.golang.org/protobuf/types/known/emptypb"

	pb "users_service/pb"
)

func (s *UserServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.UserResponse, error) {
	// Verifica a role do requisitante através do token.
	requesterRole, err := s.getRequesterRole(ctx, req.Token)
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
        return nil, status.Error(codes.PermissionDenied, "permissão negada para criar este tipo de usuário")
    }

    if req.Name == "" || req.Email == "" || req.Password == "" {
        return nil, status.Error(codes.InvalidArgument, "todos os campos são obrigatórios")
    }

	var emailExists bool
    queryCheck := `SELECT EXISTS(SELECT 1 FROM usuario WHERE email = $1)`
    err = s.DB.QueryRowContext(ctx, queryCheck, req.Email).Scan(&emailExists)
    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    if emailExists {
        return nil, status.Error(codes.AlreadyExists, "email já cadastrado")
    }
	
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
	}

	var userID int32
    tipoStr := req.UserType.String()
	query := `INSERT INTO usuario (nome, email, senha, tipo) VALUES ($1, $2, $3, $4) RETURNING id`
	err = s.DB.QueryRowContext(ctx, query, req.Name, req.Email, string(hashedPassword), tipoStr).Scan(&userID)
	if err != nil {
		return nil, status.Error(codes.Internal, "erro interno no servidor")
	}

	return &pb.UserResponse{
		UserId:   userID,
		Name:     req.Name,
		Email:    req.Email,
		UserType: req.UserType,
	}, nil
}

func (s *UserServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.UserResponse, error) {
    requesterRole, err := s.getRequesterRole(ctx, req.Token)
    if err != nil {
        return nil, err
    }

    var user pb.UserResponse
    var targetRoleStr string
    
    query := `SELECT id, nome, email, tipo FROM usuario WHERE id = $1`
    err = s.DB.QueryRowContext(ctx, query, req.UserId).Scan(&user.UserId, &user.Name, &user.Email, &targetRoleStr)
    
    if err == sql.ErrNoRows {
        return nil, status.Error(codes.NotFound, "usuário não encontrado")
    } 
    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    targetRole := stringToRole(targetRoleStr)
    user.UserType = targetRole

    // Todos podem ver o próprio perfil.
    if req.Token == req.UserId {
        return &user, nil
    }

    // Verifica se requisitante possui autorização para visualizar o usuário. 
    switch requesterRole {
    case pb.UserType_PACIENTE:
        if targetRole != pb.UserType_MEDICO {
             return nil, status.Error(codes.PermissionDenied, "acesso negado")
        }

    case pb.UserType_MEDICO:
        if targetRole != pb.UserType_PACIENTE {
            return nil, status.Error(codes.PermissionDenied, "acesso negado")
        }

    case pb.UserType_RECEPCIONISTA:
        if targetRole == pb.UserType_ADMINISTRADOR {
            return nil, status.Error(codes.PermissionDenied, "acesso negado")
        }

    case pb.UserType_ADMINISTRADOR:
        // Administrador não possui restrições de visualização.
    
    default:
        return nil, status.Error(codes.PermissionDenied, "acesso negado")
    }

    return &user, nil
}

func (s *UserServer) ListUsers(ctx context.Context, req *pb.ListUsersRequest) (*pb.ListUsersResponse, error) {
    requesterRole, err := s.getRequesterRole(ctx, req.Token)
    if err != nil {
        return nil, err
    }

    // Variáveis para montar a query dinâmica
    var query string
    var tipo string

    // Verifica se requisitante possui autorização para listar usuários. 
    switch requesterRole {
    case pb.UserType_PACIENTE:
        if req.UserType != pb.UserType_UNKNOWN_ROLE && req.UserType != pb.UserType_MEDICO {
            return nil, status.Error(codes.PermissionDenied, "acesso negado")
        }
        
        query = `SELECT id, nome, email, tipo FROM usuario WHERE tipo = 'MEDICO'`
        
    case pb.UserType_MEDICO:
        if req.UserType != pb.UserType_UNKNOWN_ROLE && req.UserType != pb.UserType_PACIENTE {
            return nil, status.Error(codes.PermissionDenied, "acesso negado")
        }

        query = `SELECT id, nome, email, tipo FROM usuario WHERE tipo = 'PACIENTE'`

    case pb.UserType_RECEPCIONISTA:
        if req.UserType == pb.UserType_ADMINISTRADOR {
            return nil, status.Error(codes.PermissionDenied, "acesso negado")
        }

        if req.UserType != pb.UserType_UNKNOWN_ROLE { // Aplicando o filtro por tipo do usuário.
            query = `SELECT id, nome, email, tipo FROM usuario WHERE tipo = $1`
            tipo = req.UserType.String()
        } else {
            query = `SELECT id, nome, email, tipo FROM usuario WHERE tipo != 'ADMINISTRADOR'`
        }

    case pb.UserType_ADMINISTRADOR:
        if req.UserType != pb.UserType_UNKNOWN_ROLE { // Aplicando o filtro por tipo do usuário.
            query = `SELECT id, nome, email, tipo FROM usuario WHERE tipo = $1`
            tipo = req.UserType.String()
        } else {
            query = `SELECT id, nome, email, tipo FROM usuario`
        }
    
    default:
        return nil, status.Error(codes.PermissionDenied, "acesso negado")
    }

    // Executa a query
    var rows *sql.Rows
    if tipo != "" {
        rows, err = s.DB.QueryContext(ctx, query, tipo)
    } else {
        rows, err = s.DB.QueryContext(ctx, query)
    }

    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }
    defer rows.Close()

    // Iteração para montar a resposta.
    var users []*pb.UserResponse
    for rows.Next() {
        var u pb.UserResponse
        var tipoStr string

        err := rows.Scan(&u.UserId, &u.Name, &u.Email, &tipoStr)
        if err != nil {
            return nil, status.Error(codes.Internal, "erro interno no servidor")
        }

        u.UserType = stringToRole(tipoStr)
        users = append(users, &u)
    }

    if err := rows.Err(); err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    return &pb.ListUsersResponse{
        Users: users,
    }, nil
}

func (s *UserServer) UpdateUser(ctx context.Context, req *pb.UpdateUserRequest) (*pb.UserResponse, error) {
    requesterRole, err := s.getRequesterRole(ctx, req.Token)
    if err != nil {
        return nil, err
    }

    var currentName, currentEmail, currentPasswordHash, targetRoleStr string

    // Busca os dados atuais do usuário
    queryTarget := `SELECT nome, email, senha, tipo FROM usuario WHERE id = $1`
    err = s.DB.QueryRowContext(ctx, queryTarget, req.UserId).Scan(&currentName, &currentEmail, &currentPasswordHash, &targetRoleStr)
    
    if err == sql.ErrNoRows {
        return nil, status.Error(codes.NotFound, "usuário não encontrado")
    } 
    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    // Verifica se requisitante possui autorização para editar o usuário. 
    allowed := false
    targetRole := stringToRole(targetRoleStr)

    if req.Token == req.UserId { // Todos podem atualizar o próprio perfil.
        allowed = true
    } else {
        switch requesterRole {
        case pb.UserType_ADMINISTRADOR:
            if targetRole != pb.UserType_PACIENTE { // Administrador não pode atualizar paciente.
                allowed = true
            }
        case pb.UserType_RECEPCIONISTA:
            if targetRole == pb.UserType_PACIENTE { // Recepcionista só pode atualizar paciente.
                allowed = true
            }
        }
    }

    if !allowed {
        return nil, status.Error(codes.PermissionDenied, "acesso negado")
    }
    
    // Se os dados para atualizar estiverem vazios, mantém os dados atuais.
    finalName := req.Name
    if finalName == "" {
        finalName = currentName
    }

    finalEmail := req.Email
    if finalEmail == "" {
        finalEmail = currentEmail
    } else if finalEmail != currentEmail { // Se for um novo email é necessário checar se já não existe.
        var emailExists bool
        checkQuery := `SELECT EXISTS(SELECT 1 FROM usuario WHERE email = $1 AND id != $2)`

        if err := s.DB.QueryRowContext(ctx, checkQuery, finalEmail, req.UserId).Scan(&emailExists); 
        err != nil {
            return nil, status.Error(codes.Internal, "erro interno no servidor")
        }

        if emailExists {
            return nil, status.Error(codes.AlreadyExists, "email já cadastrado")
        }
    }

    finalPasswordHash := currentPasswordHash
    if req.Password != "" { // Se for uma nova senha é necessário gerar um novo hash.
        hashedBytes, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
        if err != nil {
            return nil, status.Error(codes.Internal, "erro interno no servidor")
        }
        finalPasswordHash = string(hashedBytes)
    }

    updateQuery := `UPDATE usuario SET nome=$1, email=$2, senha=$3 WHERE id=$4`    
    _, err = s.DB.ExecContext(ctx, updateQuery, finalName, finalEmail, finalPasswordHash, req.UserId)
    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    return &pb.UserResponse{
        UserId:   req.UserId,
        Name:     finalName,
        Email:    finalEmail,
        UserType: targetRole,
    }, nil
}

func (s *UserServer) DeleteUser(ctx context.Context, req *pb.DeleteUserRequest) (*emptypb.Empty, error) {
    requesterRole, err := s.getRequesterRole(ctx, req.Token)
    if err != nil {
        return nil, err
    }

    var targetRoleStr string
    queryTarget := `SELECT tipo FROM usuario WHERE id = $1`
    err = s.DB.QueryRowContext(ctx, queryTarget, req.UserId).Scan(&targetRoleStr)

    if err == sql.ErrNoRows {
        return nil, status.Error(codes.NotFound, "usuário não encontrado")
    } 
    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    // Verifica se requisitante possui autorização para deletar o usuário. 
    allowed := false
    targetRole := stringToRole(targetRoleStr)
    if req.Token == req.UserId && targetRole == pb.UserType_PACIENTE {
        allowed = true
    } else {
        switch requesterRole {
        case pb.UserType_RECEPCIONISTA:
            if targetRole == pb.UserType_PACIENTE {
                allowed = true
            }

        case pb.UserType_ADMINISTRADOR:
            if targetRole == pb.UserType_MEDICO || targetRole == pb.UserType_RECEPCIONISTA {
                allowed = true
            }
        }
    }

    if !allowed {
        return nil, status.Error(codes.PermissionDenied, "acesso negado")
    }

    deleteQuery := `DELETE FROM usuario WHERE id = $1`
    _, err = s.DB.ExecContext(ctx, deleteQuery, req.UserId)
    if err != nil {
        return nil, status.Error(codes.Internal, "erro interno no servidor")
    }

    return &emptypb.Empty{}, nil
}