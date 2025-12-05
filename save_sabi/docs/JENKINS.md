# Jenkins CI/CD Pipeline Setup

This document explains how to set up and configure the Jenkins CI/CD pipeline for Save Sabi.

## Prerequisites

### Jenkins Server Requirements

1. **Jenkins Installation** (v2.350+)
2. **Required Plugins:**
   - Pipeline
   - Git
   - Docker Pipeline
   - Google Cloud SDK
   - Credentials Binding
   - JUnit
   - HTML Publisher
   - Blue Ocean (optional, for better UI)

### Install Required Plugins

```groovy
// Manage Jenkins -> Plugin Manager -> Available
// Install:
// - Pipeline
// - Docker Pipeline  
// - Google Kubernetes Engine
// - Credentials Binding Plugin
// - JUnit Plugin
// - HTML Publisher Plugin
```

## Configure Jenkins Credentials

### 1. GCP Service Account Key

1. Go to **Manage Jenkins** → **Credentials** → **System** → **Global credentials**
2. Click **Add Credentials**
3. Select **Secret file**
4. Upload your GCP service account JSON key
5. Set ID: `gcp-service-account`
6. Description: "GCP Service Account for Cloud Run deployment"

### 2. GCP Project ID

1. Add another credential
2. Select **Secret text**
3. Enter your GCP project ID
4. Set ID: `gcp-project-id`
5. Description: "GCP Project ID"

### Create GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create jenkins-deploy \
    --display-name="Jenkins Deploy Account"

# Assign roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:jenkins-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:jenkins-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:jenkins-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Download key
gcloud iam service-accounts keys create jenkins-sa-key.json \
    --iam-account=jenkins-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Pipeline Stages

### 1. Checkout
Clones the repository from GitHub.

### 2. Setup Python
Creates a virtual environment and installs dependencies using `uv`.

### 3. Lint
Runs code quality checks:
- **flake8**: Syntax errors and undefined names
- **black**: Code formatting
- **isort**: Import sorting

### 4. Test
Runs pytest with:
- JUnit XML report generation
- Coverage reporting

### 5. Security Scan
Runs security tools:
- **safety**: Checks for known vulnerabilities in dependencies
- **bandit**: Static security analysis

### 6. Build Docker Image
Builds the Docker image with build number tag.

### 7. Push to GCR (main branch only)
Pushes the Docker image to Google Container Registry.

### 8. Deploy to Cloud Run
- **develop branch**: Deploys to staging environment
- **main branch**: Deploys to production (with manual approval)

## Create the Jenkins Job

### Option 1: Multibranch Pipeline (Recommended)

1. Go to **New Item**
2. Enter name: `save-sabi`
3. Select **Multibranch Pipeline**
4. Configure:
   - **Branch Sources**: Add GitHub repository
   - **Build Configuration**: By Jenkinsfile
   - **Scan Multibranch Pipeline Triggers**: Periodically or webhook

### Option 2: Pipeline Job

1. Go to **New Item**
2. Enter name: `save-sabi`
3. Select **Pipeline**
4. Configure:
   - **Pipeline**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/manuel-Igtm/Save_sabi.git`
   - **Script Path**: `Jenkinsfile`

## GitHub Webhook Setup

### Configure Webhook

1. Go to your GitHub repository **Settings** → **Webhooks**
2. Click **Add webhook**
3. Configure:
   - **Payload URL**: `https://your-jenkins.com/github-webhook/`
   - **Content type**: `application/json`
   - **Secret**: Generate and save a secret
   - **Events**: Just the push event (or select specific events)

### Jenkins GitHub Integration

1. Go to **Manage Jenkins** → **Configure System**
2. Find **GitHub** section
3. Add GitHub Server with credentials

## Environment Variables

The pipeline uses these environment variables:

| Variable | Description | Source |
|----------|-------------|--------|
| `DOCKER_IMAGE` | Docker image name | Jenkinsfile |
| `DOCKER_TAG` | Build number as tag | Jenkinsfile |
| `GCP_PROJECT` | GCP project ID | Jenkins credentials |
| `GCR_REGISTRY` | Container registry URL | Derived |
| `CLOUD_RUN_SERVICE` | Cloud Run service name | Jenkinsfile |
| `CLOUD_RUN_REGION` | GCP region | Jenkinsfile |

## Required Jenkins Tools

Configure these in **Manage Jenkins** → **Global Tool Configuration**:

### Docker

```yaml
Name: docker
Install automatically: Yes
```

### Google Cloud SDK

Install on Jenkins agent:

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

## Troubleshooting

### Common Issues

#### 1. Docker permission denied

```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

#### 2. gcloud not found

Ensure Google Cloud SDK is in PATH:

```groovy
environment {
    PATH = "/usr/local/google-cloud-sdk/bin:${env.PATH}"
}
```

#### 3. Python version issues

Use pyenv or specify Python path:

```groovy
sh '''
    /usr/bin/python3.10 -m venv .venv
    . .venv/bin/activate
'''
```

#### 4. Test failures

Check environment variables are set:

```groovy
sh '''
    export USE_SQLITE=True
    export USE_LOCAL_CACHE=True
    export DJANGO_SETTINGS_MODULE=save_sabi.settings
    pytest -v
'''
```

## Monitoring

### Build Notifications

Add to `post` block in Jenkinsfile:

```groovy
post {
    success {
        slackSend(
            color: 'good',
            message: "Build succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        )
    }
    failure {
        slackSend(
            color: 'danger',
            message: "Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        )
    }
}
```

### Dashboard

1. Install **Blue Ocean** plugin for better visualization
2. Access via: `https://your-jenkins.com/blue/`

## Local Testing

Test the pipeline locally using Jenkins CLI:

```bash
# Download jenkins-cli.jar
wget https://your-jenkins.com/jnlpJars/jenkins-cli.jar

# Test syntax
java -jar jenkins-cli.jar -s https://your-jenkins.com/ \
    -auth user:token \
    declarative-linter < Jenkinsfile
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use Jenkins credentials** for all sensitive data
3. **Restrict branch access** for production deployments
4. **Enable audit logging** in Jenkins
5. **Regular security updates** for Jenkins and plugins
6. **Use HTTPS** for Jenkins server
7. **Implement RBAC** for Jenkins users

## Pipeline Customization

### Skip Stages

Use when conditions:

```groovy
stage('Deploy') {
    when {
        not { changeRequest() }
        branch 'main'
    }
    steps {
        // Deploy
    }
}
```

### Parallel Execution

```groovy
stage('Quality Checks') {
    parallel {
        stage('Lint') {
            steps { sh 'flake8 .' }
        }
        stage('Security') {
            steps { sh 'bandit -r .' }
        }
    }
}
```

### Matrix Builds

```groovy
matrix {
    axes {
        axis {
            name 'PYTHON_VERSION'
            values '3.10', '3.11', '3.12'
        }
    }
    stages {
        stage('Test') {
            steps {
                sh "python${PYTHON_VERSION} -m pytest"
            }
        }
    }
}
```
