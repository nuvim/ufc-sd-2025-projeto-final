import requests
import sys
import json

# URL base da API REST (Aponta para a Interface Python e não para o Go direto)
BASE_URL = "http://localhost:5000"

def create_user(name, email, password, user_type, cpf="", phone=""):
    url = f"{BASE_URL}/users"
    data = {
        "name": name,
        "email": email,
        "password": password,
        "user_type": user_type,
        "cpf": cpf,
        "phone": phone
    }
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def get_user(user_id):
    url = f"{BASE_URL}/users/{user_id}"
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def delete_user(user_id):
    url = f"{BASE_URL}/users/{user_id}"
    response = requests.delete(url)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def list_users(user_type="", limit=50):
    url = f"{BASE_URL}/users"
    params = {"limit": limit}
    if user_type:
        params["user_type"] = user_type
    
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def authenticate_user(email, password):
    url = f"{BASE_URL}/auth/login"
    data = {"email": email, "password": password}
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def main():
    if len(sys.argv) < 2:
        print("Uso: python meu_teste.py <comando> [args...]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "create":
            create_user(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif command == "login":
            authenticate_user(sys.argv[2], sys.argv[3])
        elif command == "get":
            get_user(sys.argv[2])
        elif command == "list":
            list_users()
        elif command == "delete":
            delete_user(sys.argv[2])
        else:
            print("Comando inválido")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()