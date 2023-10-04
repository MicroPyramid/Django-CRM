pipeline {
    agent any

    environment {
        ENV_TYPE = "dev"
        APP_NAME = "bottlecrm-api"
        DOCKERHUB = credentials("dockerhub")
        DOCKER_IMAGE_TAG = "build-${env.BUILD_NUMBER}-${env.GIT_COMMIT[0..7]}"
        DOCKER_IMAGE = "ashwin31/django-crm:${env.DOCKER_IMAGE_TAG}"
        DOCKER_CONFIG = "config.json"
    }

    stages {
        stage("build") {
            steps {
                sh "pwd; whoami; ls -al;"
                sh "docker build --build-arg APP_NAME=$APP_NAME -t ${env.DOCKER_IMAGE} ."
            }
        }

        stage("push") {
            steps {
                sh "echo '$DOCKERHUB_PSW' | docker login -u $DOCKERHUB_USR --password-stdin"
                sh "docker push ${env.DOCKER_IMAGE}"
            }
        }
        stage('trigger deploy') {
            steps {
                build job: 'deploy', parameters: [
                    string(
                        name: 'ENV_TYPE',
                        value: "${env.ENV_TYPE}"
                    ),
                    string(
                        name: 'APP_NAME',
                        value: "${env.APP_NAME}"
                    ),
                    string(
                        name: 'DOCKER_IMAGE',
                        value: "${env.DOCKER_IMAGE}"
                    )
                ]
            }
        }
    }

    post {
        always {
            cleanWs()
            dir("${env.WORKSPACE}@tmp") {
                deleteDir()
            }
            dir("${env.WORKSPACE}@script") {
                deleteDir()
            }
            dir("${env.WORKSPACE}@script@tmp") {
                deleteDir()
            }
            sh 'docker rmi $(docker images -aq) || true'
        }
    }
}
