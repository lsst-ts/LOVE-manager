pipeline {
  agent any

  environment {
    registry = "inriachile/love-manager"
    registryCredential = "dockerhub-inriachile"
    dockerImage = registry + ":$GIT_BRANCH"
  }

  triggers {
    pollSCM("* * * * *")
  }
  stages {
    stage("Build Docker image") {
      steps {
        script {
          docker.build dockerImage
        }
      }
    }
    stage("Push Docker image") {
      steps {
        script {
          docker.withRegistry("", registryCredential) {
            dockerImage.push()
          }
        }
      }
    }
  }
}
