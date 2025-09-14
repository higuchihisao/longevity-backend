# Longevity Backend

Backend Django para aplicación de proyección financiera personal con análisis de longevidad.

## 🚀 Características

- **Autenticación JWT** con djangorestframework-simplejwt
- **Modelos financieros completos** para cuentas, inversiones, gastos e ingresos
- **API REST** con Django REST Framework
- **Proyecciones financieras** determinísticas
- **Soporte multi-moneda** (PEN, USD, EUR)
- **CORS configurado** para integración con frontend

## 📋 Requisitos

- Python 3.12+
- Django 5.0.8
- PostgreSQL (opcional, SQLite por defecto)

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/longevity_backend.git
cd longevity_backend
```

2. **Crear entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```bash
python manage.py migrate
```

5. **Crear superusuario**
```bash
python manage.py createsuperuser
```

6. **Cargar datos de prueba**
```bash
python manage.py seed_data
```

7. **Ejecutar servidor**
```bash
python manage.py runserver
```

## 📚 API Endpoints

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/register/` - Registrarse
- `POST /api/auth/logout/` - Cerrar sesión
- `POST /api/auth/refresh/` - Renovar token
- `GET /api/auth/user/` - Obtener perfil de usuario
- `PUT /api/auth/user/update/` - Actualizar perfil

### Portafolio
- `GET /api/accounts/` - Listar cuentas
- `POST /api/accounts/` - Crear cuenta
- `GET /api/securities/` - Listar valores
- `POST /api/securities/` - Crear valor
- `GET /api/holdings/` - Listar inversiones
- `POST /api/holdings/` - Crear inversión

### Datos Financieros
- `GET /api/profiles/` - Perfiles de usuario
- `GET /api/income/` - Fuentes de ingreso
- `GET /api/expenses/` - Gastos
- `GET /api/assumptions/` - Supuestos financieros

### Proyecciones
- `POST /api/projections/runs/` - Crear proyección
- `POST /api/projections/runs/{id}/execute/` - Ejecutar proyección
- `GET /api/summary/longevity/` - Resumen de longevidad

## 🔧 Configuración

### Variables de Entorno
Crear archivo `.env`:
```env
SECRET_KEY=tu-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### CORS
Configurado para:
- `http://localhost:3000` (desarrollo)
- `https://app.lovable.dev` (Lovable)

## 📊 Modelos

### Usuario
- **User**: Modelo personalizado con email como username
- **Profile**: Información financiera del usuario

### Financiero
- **Account**: Cuentas bancarias y de inversión
- **Security**: Valores e instrumentos financieros
- **Holding**: Inversiones del usuario
- **Transaction**: Transacciones financieras
- **IncomeSource**: Fuentes de ingreso
- **Expense**: Gastos del usuario
- **Assumptions**: Supuestos para proyecciones

### Proyecciones
- **ProjectionRun**: Ejecución de proyección
- **ProjectionYear**: Datos año por año

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Verificar datos
python manage.py check_data
```

## 📝 Comandos de Gestión

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Cargar datos de prueba
python manage.py seed_data

# Verificar datos
python manage.py check_data
```

## 🚀 Despliegue

### Docker
```bash
docker build -t longevity-backend .
docker run -p 8000:8000 longevity-backend
```

### Heroku
```bash
# Instalar Heroku CLI
# Crear app
heroku create tu-app-name

# Configurar variables
heroku config:set SECRET_KEY=tu-secret-key
heroku config:set DEBUG=False

# Desplegar
git push heroku main
```

## 📄 Licencia

MIT License

## 👥 Contribuir

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📞 Soporte

Para soporte, contactar a [tu-email@ejemplo.com]