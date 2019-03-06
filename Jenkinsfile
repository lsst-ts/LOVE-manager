pipeline {
  agent any

  environment {
    registry = "inriachile/love-manager"
  }

  triggers {
    pollSCM('* * * * *')
  }
  stages {
    stage('Build') {
      steps {
        echo 'Building Docker image'
        script {
          docker.build registry + ":$GIT_BRANCH"
        }
      }
    }
  }
}
