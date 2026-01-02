package database

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	_ "github.com/lib/pq" // Driver do postgreSQL
)

// Cria a conexão com o banco de dados.
func NewConnection() (*sql.DB, error) {
	// Lê as variáveis de ambiente do Docker.
	host := os.Getenv("DB_HOST")
	port := os.Getenv("DB_PORT")
	user := os.Getenv("DB_USER")
	password := os.Getenv("DB_PASSWORD")
	dbname := os.Getenv("DB_NAME")

	// Monta a string de conexão
	psqlInfo := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable", host, port, user, password, dbname)

	// Abre o driver
	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		return nil, fmt.Errorf("erro ao configurar driver: %v", err)
	}

	// Conecta-se ao banco de dados.
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, fmt.Errorf("erro ao conectar no banco (Ping): %v", err)
	}

	log.Println("Conectado ao banco de dados.")

	return db, nil
}