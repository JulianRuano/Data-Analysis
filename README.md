## 1. Crear el Entorno Virtual

**En Windows:**

```bash
python -m venv env

```

**En Linux / macOS:**

```bash
python3 -m venv env

```

## 2. Activar el Entorno Virtual


**En Windows (Símbolo del sistema / CMD):**

```cmd
env\Scripts\activate.bat

```

**En Windows (PowerShell):**

```powershell
.\env\Scripts\Activate.ps1

```

**En Linux / macOS:**

```bash
source env/bin/activate

```

## 3. Desactivar el Entorno Virtual

Cuando termines de trabajar y quieras volver al entorno global de Python en tu sistema, simplemente ejecuta:

```bash
deactivate

```

---

## Solución a Errores Comunes

### Windows: "La ejecución de scripts está deshabilitada en este sistema"

**Causa:** Las políticas de seguridad predeterminadas de PowerShell bloquean la ejecución de scripts (como el archivo `Activate.ps1`).
**Solución:**


Ejecuta el siguiente comando para permitir la ejecución de scripts localmente de forma segura:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

```


### Linux (Ubuntu/Debian): "The virtual environment was not created successfully" o "No module named venv"

**Causa:** Algunas distribuciones basadas en Debian/Ubuntu separan el módulo `venv` de la instalación base de Python para ahorrar espacio.
**Solución:** Instala el paquete de entornos virtuales de Python mediante el gestor de paquetes de tu sistema:

```bash
sudo apt update
sudo apt install python3-venv

```

# requirements

```bash
pip install -r requirements.txt
```