pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        COMPOSE_PROJECT_NAME = 'musiclib'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare .env') {
            steps {
                // Credential type "Secret file" berisi isi .env (DB_NAME, DB_USER, DB_PASSWORD)
                withCredentials([file(credentialsId: 'music-env-file', variable: 'ENV_FILE')]) {
                    sh '''
                        umask 077
                        cp "$ENV_FILE" .env
                    '''
                }
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    test -f db/tracks.csv || { echo "db/tracks.csv tidak ada (jalankan clean_dataset.py dulu)"; exit 1; }
                    python3 -m py_compile backend/app.py
                    docker compose config -q
                '''
            }
        }

        stage('Build') {
            steps {
                sh 'docker compose build --pull'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker compose up -d --remove-orphans'
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if docker compose exec -T backend python -c \
                            "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/filters', timeout=5)"; then
                            echo "Backend sehat"
                            exit 0
                        fi
                        echo "Menunggu backend... ($i/15)"
                        sleep 5
                    done
                    echo "Backend tidak merespons"
                    exit 1
                '''
            }
        }
    }

    post {
        failure {
            sh 'docker compose ps || true'
            sh 'docker compose logs --tail=50 || true'
        }
        always {
            sh 'docker image prune -f || true'
        }
    }
}