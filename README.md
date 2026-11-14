# UniPass · Sistema de Control de Acceso de Bicicletas Universitario

Plataforma web desarrollada en **Django 5.2** para la gestión de usuarios, asignación de bicicletas con código QR único (`UUID4`) y control de entradas y salidas en tiempo real.

## Guía de Instalación y Despliegue (Procedimiento del Instalador)

### 1. Crear y activar el ambiente virtual
```bash
python -m venv venv

# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# En Linux / macOS:
source venv/bin/activate
```

### 2. Instalar las dependencias del proyecto
```bash
pip install -r requirements.txt
```

### 3. Configurar el entorno y la base de datos
Copiar el archivo de variables de entorno de ejemplo y aplicar las migraciones:
```bash
# En Windows (PowerShell / CMD):
copy .env.example .env

# En Linux / macOS:
cp .env.example .env

python manage.py migrate
```
*(Opcional: Si se desea crear un superadministrador nuevo desde cero, ejecutar `python manage.py createsuperuser`).*

### 4. Ejecutar las pruebas automatizadas (Verificación de seguridad)
```bash
python manage.py test
```

### 5. Levantar el servicio web
```bash
python manage.py runserver
```
El sistema quedará disponible en `http://127.0.0.1:8000/`.

---

## Credenciales de Acceso (Base de datos precargada)

El repositorio incluye una base de datos SQLite lista para pruebas inmediatas con los siguientes perfiles:

| Rol | Usuario | Contraseña |
| :--- | :--- | :--- |
| Administrador | `admin1` | `AdminPassword123!` |
| Guardia / Vigilancia | `guardia1` | `Password123!` |
| Estudiante / Usuario | `213110229` | `UniPass2026!` |

---

