# Integración Frontend - Longevity Backend

## Información de Conexión

**URL Base**: `http://localhost:8000/api/`

## Autenticación

### 1. Registro de Usuario

**Endpoint**: `POST /api/auth/register/`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123",
  "first_name": "Nombre",
  "last_name": "Apellido"
}
```

**Respuesta exitosa** (201):
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "is_active": true,
    "date_joined": "2025-09-14T16:39:55.155528Z"
  }
}
```

**Errores posibles** (400):
```json
{"error": "Email is required"}
{"error": "Password is required"}
{"error": "Please enter a valid email address"}
{"error": "Password must be at least 6 characters long"}
{"error": "User with this email already exists"}
```

### 2. Login

**Endpoint**: `POST /api/auth/login/`

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

**Respuesta exitosa** (200):
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "is_active": true,
    "date_joined": "2025-09-14T16:39:55.155528Z"
  }
}
```

### 3. Requests Autenticados

**Headers requeridos**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Ejemplo de Implementación en JavaScript/React

```javascript
// Configuración base
const API_BASE_URL = 'http://localhost:8000/api';

// Función para hacer requests autenticados
const authenticatedRequest = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Request failed');
  }
  
  return response.json();
};

// Registro
const register = async (userData) => {
  const response = await fetch(`${API_BASE_URL}/auth/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Registration failed');
  }
  
  const data = await response.json();
  
  // Guardar tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  return data;
};

// Login
const login = async (email, password) => {
  const response = await fetch(`${API_BASE_URL}/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Login failed');
  }
  
  const data = await response.json();
  
  // Guardar tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  return data;
};

// Logout
const logout = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (refreshToken) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }
  
  // Limpiar localStorage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

// Refresh token
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  
  if (!refresh) {
    throw new Error('No refresh token available');
  }
  
  const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  });
  
  if (!response.ok) {
    throw new Error('Token refresh failed');
  }
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  
  return data.access;
};

// Ejemplo de uso con manejo de errores
const handleRegister = async (formData) => {
  try {
    const result = await register(formData);
    console.log('Registration successful:', result);
    // Redirigir al dashboard
  } catch (error) {
    console.error('Registration error:', error.message);
    // Mostrar error al usuario
    alert(error.message);
  }
};

const handleLogin = async (email, password) => {
  try {
    const result = await login(email, password);
    console.log('Login successful:', result);
    // Redirigir al dashboard
  } catch (error) {
    console.error('Login error:', error.message);
    // Mostrar error al usuario
    alert(error.message);
  }
};
```

## Endpoints Principales

### Perfil de Usuario
- `GET /api/profiles/` - Listar perfiles
- `POST /api/profiles/` - Crear perfil
- `GET /api/profiles/{id}/` - Obtener perfil
- `PUT /api/profiles/{id}/` - Actualizar perfil

### Ingresos
- `GET /api/income/` - Listar fuentes de ingreso
- `POST /api/income/` - Crear fuente de ingreso
- `PUT /api/income/{id}/` - Actualizar fuente de ingreso
- `DELETE /api/income/{id}/` - Eliminar fuente de ingreso

### Gastos
- `GET /api/expenses/` - Listar gastos
- `POST /api/expenses/` - Crear gasto
- `PUT /api/expenses/{id}/` - Actualizar gasto
- `DELETE /api/expenses/{id}/` - Eliminar gasto

### Cuentas
- `GET /api/accounts/` - Listar cuentas
- `POST /api/accounts/` - Crear cuenta
- `PUT /api/accounts/{id}/` - Actualizar cuenta
- `DELETE /api/accounts/{id}/` - Eliminar cuenta

### Resumen de Longevidad
- `GET /api/summary/longevity/` - Obtener resumen financiero

## Códigos de Error Comunes

- **400 Bad Request**: Datos de entrada inválidos
- **401 Unauthorized**: Token de acceso inválido o expirado
- **403 Forbidden**: No tienes permisos para esta acción
- **404 Not Found**: Recurso no encontrado
- **500 Internal Server Error**: Error del servidor

## Notas Importantes

1. **Tokens JWT**: Los access tokens duran 60 minutos, los refresh tokens duran 7 días
2. **CORS**: Configurado para `localhost:3000` y `app.lovable.dev`
3. **Validación**: El backend valida email, contraseña (mínimo 6 caracteres) y campos requeridos
4. **Manejo de errores**: Siempre revisa el campo `error` en las respuestas de error
5. **Content-Type**: Siempre incluye `application/json` en los headers

## Testing

Puedes probar los endpoints con curl:

```bash
# Registro
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "first_name": "Test", "last_name": "User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# Request autenticado
curl -X GET http://localhost:8000/api/profiles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
