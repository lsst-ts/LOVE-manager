pipeline {
  agent any

  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "inriachile/love-manager:${GIT_BRANCH}"
  }

  triggers {
    pollSCM("* * * * *")
  }
  stages {
    def dockerImage = null
    stage("Build Docker image") {
      steps {
        script {
          dockerImage = docker.build dockerImageName
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
