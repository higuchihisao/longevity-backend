# Autenticación API - Longevity Backend

## Información para el Frontend

### URL Base del Backend
```
http://localhost:8000/api/
```

### Endpoints de Autenticación

#### 1. Login
- **URL**: `POST /api/auth/login/`
- **Descripción**: Iniciar sesión con email y contraseña
- **Body**:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "tu_contraseña"
}
```
- **Respuesta exitosa** (200):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "is_active": true,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

#### 2. Register
- **URL**: `POST /api/auth/register/`
- **Descripción**: Registrar nuevo usuario
- **Body**:
```json
{
  "email": "nuevo@ejemplo.com",
  "password": "contraseña_segura",
  "first_name": "María",
  "last_name": "García"
}
```
- **Respuesta exitosa** (201):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 2,
    "email": "nuevo@ejemplo.com",
    "first_name": "María",
    "last_name": "García",
    "is_active": true,
    "date_joined": "2024-01-15T10:30:00Z"
  }
}
```

#### 3. Logout
- **URL**: `POST /api/auth/logout/`
- **Descripción**: Cerrar sesión (invalidar refresh token)
- **Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
- **Respuesta exitosa** (200):
```json
{
  "message": "Successfully logged out"
}
```

#### 4. Refresh Token
- **URL**: `POST /api/auth/refresh/`
- **Descripción**: Renovar access token usando refresh token
- **Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
- **Respuesta exitosa** (200):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 5. User Profile
- **URL**: `GET /api/auth/user/`
- **Descripción**: Obtener perfil del usuario actual
- **Headers**: `Authorization: Bearer <access_token>`
- **Respuesta exitosa** (200):
```json
{
  "id": 1,
  "email": "usuario@ejemplo.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z"
}
```

#### 6. Update Profile
- **URL**: `PUT /api/auth/user/update/`
- **Descripción**: Actualizar perfil del usuario
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
```json
{
  "first_name": "Juan Carlos",
  "last_name": "Pérez García",
  "email": "nuevo_email@ejemplo.com"
}
```
- **Respuesta exitosa** (200):
```json
{
  "id": 1,
  "email": "nuevo_email@ejemplo.com",
  "first_name": "Juan Carlos",
  "last_name": "Pérez García",
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z"
}
```

### Tipo de Autenticación
- **JWT Tokens** con djangorestframework-simplejwt
- **Access Token**: Válido por 60 minutos
- **Refresh Token**: Válido por 7 días
- **Header**: `Authorization: Bearer <access_token>`

### CORS Configurado
- ✅ **Orígenes permitidos**: 
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `https://app.lovable.dev`
- ✅ **Credentials**: Habilitado
- ✅ **Headers permitidos**: authorization, content-type, etc.

### Ejemplo de Uso en Frontend

#### JavaScript/React
```javascript
// Login
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Guardar tokens
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
  }
  
  return data;
};

// Hacer requests autenticados
const authenticatedRequest = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
};

// Refresh token
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/api/auth/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('access_token', data.access);
  }
  
  return data;
};
```

### Códigos de Error Comunes

#### 400 Bad Request
```json
{
  "error": "Email and password are required"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid"
}
```

#### 400 Bad Request (Email ya existe)
```json
{
  "error": "User with this email already exists"
}
```

### Testing con cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "password123"}'

# Request autenticado
curl -X GET http://localhost:8000/api/profiles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```
