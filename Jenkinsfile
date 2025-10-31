pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t pytube-app .'
            }
        }
        stage('Test') {
            steps {
                sh 'python manage.py test'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker run -d -p 8000:8000 pytube-app'
            }
        }
    }
}
