pipeline {
  agent any

  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImage = "inriachile/love-manager:${GIT_BRANCH}"
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
