pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'save-sabi'
        DOCKER_TAG = "${BUILD_NUMBER}"
        GCP_PROJECT = credentials('gcp-project-id')
        GCR_REGISTRY = "gcr.io/${GCP_PROJECT}"
        CLOUD_RUN_SERVICE = 'save-sabi'
        CLOUD_RUN_REGION = 'us-central1'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -5'
            }
        }
        
        stage('Setup Python') {
            steps {
                dir('save_sabi') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install --upgrade pip
                        pip install uv
                        uv pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Lint') {
            steps {
                dir('save_sabi') {
                    sh '''
                        . .venv/bin/activate
                        echo "Running flake8..."
                        flake8 core/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
                        echo "Running black check..."
                        black --check core/ --diff || true
                        echo "Running isort check..."
                        isort --check-only core/ --diff || true
                    '''
                }
            }
        }
        
        stage('Test') {
            steps {
                dir('save_sabi') {
                    sh '''
                        . .venv/bin/activate
                        export USE_SQLITE=True
                        export USE_LOCAL_CACHE=True
                        export DJANGO_SETTINGS_MODULE=save_sabi.settings
                        pytest --junitxml=test-results.xml --cov=core --cov-report=xml:coverage.xml -v
                    '''
                }
            }
            post {
                always {
                    dir('save_sabi') {
                        junit 'test-results.xml'
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: '.',
                            reportFiles: 'coverage.xml',
                            reportName: 'Coverage Report'
                        ])
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                dir('save_sabi') {
                    sh '''
                        . .venv/bin/activate
                        pip install safety bandit
                        echo "Running safety check..."
                        safety check -r requirements.txt || true
                        echo "Running bandit security scan..."
                        bandit -r core/ -f json -o bandit-report.json || true
                    '''
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                dir('save_sabi') {
                    sh '''
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }
        
        stage('Push to GCR') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=${GCP_KEY}
                        gcloud auth configure-docker --quiet
                        
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${GCR_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${GCR_REGISTRY}/${DOCKER_IMAGE}:latest
                        
                        docker push ${GCR_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push ${GCR_REGISTRY}/${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }
        
        stage('Deploy to Cloud Run (Staging)') {
            when {
                branch 'develop'
            }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=${GCP_KEY}
                        gcloud config set project ${GCP_PROJECT}
                        
                        gcloud run deploy ${CLOUD_RUN_SERVICE}-staging \
                            --image ${GCR_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --platform managed \
                            --region ${CLOUD_RUN_REGION} \
                            --allow-unauthenticated \
                            --set-env-vars="DEBUG=True" \
                            --memory 512Mi \
                            --min-instances 0 \
                            --max-instances 3
                    '''
                }
            }
        }
        
        stage('Deploy to Cloud Run (Production)') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=${GCP_KEY}
                        gcloud config set project ${GCP_PROJECT}
                        
                        # Run migrations first
                        gcloud run jobs execute save-sabi-migrate --region ${CLOUD_RUN_REGION} --wait || true
                        
                        # Deploy to production
                        gcloud run deploy ${CLOUD_RUN_SERVICE} \
                            --image ${GCR_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --platform managed \
                            --region ${CLOUD_RUN_REGION} \
                            --allow-unauthenticated \
                            --set-env-vars="DEBUG=False" \
                            --memory 512Mi \
                            --cpu 1 \
                            --min-instances 1 \
                            --max-instances 10 \
                            --concurrency 80
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
            // Notify on success (Slack, email, etc.)
        }
        failure {
            echo 'Pipeline failed!'
            // Notify on failure
        }
    }
}
