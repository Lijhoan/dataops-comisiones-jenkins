# DataOps - Python ✕ Docker ✕ Jenkins  
Proceso automático de cálculo de comisiones. d
 
--- Cambio

## 1. Descripción

Este proyecto ejecuta, de forma **100 % automatizada**, el flujo mensual de cálculo de comisiones:

1. **Ingesta**  
   - Lee el CSV `ComisionEmpleados_V1_<AAAAMM>.csv` correspondiente al mes en curso.
   - Extrae la tabla **`rrhh.empleado`** desde PostgreSQL.

2. **Transformación**  
   - Normaliza valores numéricos.  
   - Calcula la comisión por empleado.  

3. **Salida**  
   - Exporta el resultado a **Excel** (`ComisionesCalculadas.xlsx`).  
   - Envía el archivo por e-mail al destinatario configurado.

4. **Orquestación**  
   - Todo el código corre dentro de un contenedor **Docker** reproducible.  
   - Un **pipeline de Jenkins** se encarga de compilar la imagen, ejecutar el job y publicar artefactos.

---

## 2. Arquitectura

```

┌──────────────┐    docker run    ┌────────────────┐
│ Jenkins Job  │ ───────────────► │  Contenedor    │
│  (pipeline)  │                  │  Python 3.11   │
└──────────────┘                  │                │
▲                                 │ 1. Lee CSV     │
│                                 │ 2. Lee PG      │
│  logs / artefactos              │ 3. Calcula     │
└─────────────────────────────────│ 4. Excel+e-mail│
                                  └────────────────┘

```

---

## 3. Tecnologías

| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python     | 3.11    | Transformaciones y lógica de negocio |
| Pandas     | 2.x     | Procesamiento de datos tabulares     |
| psycopg2-binary | 2.9 | Conexión PostgreSQL                 |
| openpyxl   | 3.x     | Exportar a Excel                     |
| Docker     | 24+     | Aislamiento y portabilidad           |
| Jenkins    | 2.452+  | CI/CD y orquestación DataOps         |
| Mailtrap   | (sandbox) | Envío seguro de correos en pruebas |

---

## 4. Estructura de carpetas

```

.
├─ app/
│  ├─ main.py          # script principal
│  ├─ config.json      # credenciales y rutas (NO commitear prod)
│  └─ requirements.txt
├─ data/               # aquí se montan los CSV de cada mes
├─ Dockerfile
└─ Jenkinsfile

````

---

## 5. Prerequisitos

| Requisito | Notas |
|-----------|-------|
| Docker Engine | activo y con permisos para compilar imágenes |
| Jenkins agent | con acceso a Docker / Podman |
| PostgreSQL | tabla `rrhh.empleado` accesible desde el runner |
| Mailtrap (sandbox) | para pruebas de e-mail sin riesgo |
| Variable `CONFIG_FILE` | (opcional) ruta al `config.json` dentro del contenedor |

---

## 6. Archivo `config.json` de ejemplo

```jsonc
{
  "db": {
    "host": "HOST_DE_BD",
    "port": 5432,
    "dbname": "dmc",
    "user": "USUARIO_BD",
    "password": "PASSWORD_BD"
  },
  "smtp": {
    "server": "sandbox.smtp.mailtrap.io",
    "port": 587,
    "user": "USUARIO_SMTP",
    "password": "PASSWORD_SMTP",
    "sender_email": "Python DataOps <pydataops@example.com>"
  },
  "paths": {
    "csv_dir": "/app/data",
    "excel": "ComisionesCalculadas.xlsx"
  },
  "report": {
    "to": "finanzas@example.com",
    "subject": "Comisiones Calculadas",
    "body_html": "Adjunto reporte de comisiones mensuales.<br>Saludos."
  }
}
````

> **Seguridad :** monta el JSON como *secret* (Docker Swarm) o credencial de Jenkins; evita incluirlo en el repositorio.

---

## 7. Construcción y prueba local

```bash
# clonar
git clone https://github.com/tu-org/dataops-comisiones.git
cd dataops-comisiones

# compilar imagen
docker build -t dataops/comisiones:latest .

# prueba en local (monta CSV y config)
docker run --rm \
  -v "$PWD/config.json:/app/config.json:ro" \
  -v "$PWD/data:/app/data:ro" \
  dataops/comisiones:latest
```

---

## 8. Pipeline Jenkins (ejemplo)

```groovy
pipeline {
  agent any
  environment {
    IMAGE = "registry.example.com/dataops/comisiones:${env.BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Build') {
      steps {
        sh 'docker build -t $IMAGE .'
      }
    }

    stage('Test job') {
      steps {
        sh '''
          docker run --rm \
            -v $WORKSPACE/config.json:/app/config.json:ro \
            -v $WORKSPACE/data:/app/data:ro \
            $IMAGE
        '''
      }
    }

    stage('Push image') {
      when { branch 'main' }
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry-creds',
                                          usernameVariable: 'REG_USER',
                                          passwordVariable: 'REG_PASS')]) {
          sh '''
            echo $REG_PASS | docker login registry.example.com -u $REG_USER --password-stdin
            docker push $IMAGE
          '''
        }
      }
    }
  }

  post {
    success {
      archiveArtifacts artifacts: 'ComisionesCalculadas.xlsx', fingerprint: true
    }
  }
}
```

* El stage **Test job** ejecuta el contenedor con los archivos de prueba.
* El artefacto Excel se publica en Jenkins para descarga inmediata.

---

## 9. Extensiones sugeridas

| Idea                                                             | Valor                                          |
| ---------------------------------------------------------------- | ---------------------------------------------- |
| Desplegar en **AWS Fargate** o **Kubernetes CronJob**            | Escalabilidad sin servidores Jenkins dedicados |
| Reemplazar Mailtrap por **SES / SendGrid** para producción       | Envío de correos en masa                       |
| Añadir tests unitarios con **pytest** y cobertura en el pipeline | Calidad de código                              |
| Incluir **alertas Slack** tras cada ejecución                    | visibilidad del proceso DataOps                |
| Parametrizar el período para reprocesos manuales                 | flexibilidad operacional                       |

---

## 10. Licencia

DMC © 2025 — Miguelangel / DMC Institute
Se permite uso comercial y modificación bajo los términos de la licencia.

# reporte_comisiones
