pipeline {
  agent any
  environment {
    registryCredential = "dockerhub-inriachile"
    dockerImageName = "inriachile/love-manager:${GIT_BRANCH}"
    dockerImage = ""
  }
  triggers {
    pollSCM("* * * * *")
  }
  when {
    branch "ci-develop"
  }
  stages {
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
