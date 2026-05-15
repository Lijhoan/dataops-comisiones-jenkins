pipeline {
    agent any

    parameters {
        string(name: 'MES_PROCESO', defaultValue: '202605', description: 'Mes a procesar en formato AAAAMM')
    }

    environment {
        IMAGE_NAME = 'dataops/comisiones'
        IMAGE_TAG = "${BUILD_NUMBER}"
        CONTAINER_OUTPUT = '/app/output/ComisionesCalculadas.xlsx'
        LOCAL_OUTPUT = 'output/ComisionesCalculadas.xlsx'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Descargando codigo desde el repositorio...'
                checkout scm
            }
        }

        stage('Validate workspace') {
            steps {
                echo 'Validando archivos requeridos...'
                sh '''
                    set -e
                    test -f Dockerfile
                    test -f app/main.py
                    test -f app/requirements.txt
                    test -f data/ComisionEmpleados_V1_${MES_PROCESO}.csv
                    mkdir -p output
                    echo "Archivos requeridos validados correctamente."
                '''
            }
        }

        stage('Prepare config') {
            steps {
                echo 'Preparando config.json para ejecucion del contenedor...'
                script {
                    if (fileExists('config.json')) {
                        echo 'Se usara config.json existente en el workspace.'
                    } else {
                        withCredentials([file(credentialsId: 'dataops-config-json', variable: 'CONFIG_JSON_FILE')]) {
                            sh 'cp "$CONFIG_JSON_FILE" config.json'
                        }
                    }
                }
            }
        }

        stage('Build Docker image') {
            steps {
                echo 'Construyendo imagen Docker...'
                sh '''
                    set -e
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Run commissions container') {
            steps {
                echo 'Ejecutando contenedor de calculo de comisiones...'
                sh '''
                    set -e
                    docker run --rm \
                        -v "$WORKSPACE/config.json:/app/config.json:ro" \
                        -v "$WORKSPACE/data:/app/data:ro" \
                        -v "$WORKSPACE/output:/app/output" \
                        -e MES_PROCESO_APP=${MES_PROCESO} \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Verify output') {
            steps {
                echo 'Verificando Excel generado...'
                sh '''
                    set -e
                    test -f ${LOCAL_OUTPUT}
                    ls -lh ${LOCAL_OUTPUT}
                    echo "Excel generado correctamente: ${LOCAL_OUTPUT}"
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline completado exitosamente. Artefacto generado: ${LOCAL_OUTPUT}"
            archiveArtifacts artifacts: 'output/ComisionesCalculadas.xlsx', fingerprint: true
        }

        failure {
            echo 'Pipeline fallido. Revisar Console Output.'
        }

        always {
            echo 'Fin de ejecucion del pipeline DataOps Jenkins + Docker.'
        }
    }
}
